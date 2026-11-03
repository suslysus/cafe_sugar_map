-- Supabase SQL Editor의 postgres 역할에서 실행한다.
-- 가상 사용자 2명을 트랜잭션 안에서만 생성하고 마지막에 ROLLBACK한다.
-- 실제 이메일 발송·비밀번호 생성·기존 사용자 수정은 하지 않는다.
begin;
insert into auth.users (id, email, raw_user_meta_data)
values
  ('f0000000-0000-4000-8000-000000000001', 'csm-rls-a@example.invalid', '{"display_name":"RLS A"}'),
  ('f0000000-0000-4000-8000-000000000002', 'csm-rls-b@example.invalid', '{"display_name":"RLS B"}');
insert into public.favorites (user_id, menu_id)
values ('f0000000-0000-4000-8000-000000000002', 'demo-h-milk');

set local role authenticated;
select set_config('request.jwt.claim.sub', 'f0000000-0000-4000-8000-000000000001', true);
select set_config('request.jwt.claims', '{"sub":"f0000000-0000-4000-8000-000000000001","role":"authenticated"}', true);
do $$
declare changed integer;
begin
  assert (select count(*) from public.profiles) = 1, 'A must see only its own profile';
  assert (select count(*) from public.favorites) = 0, 'A must not see B favorites';
  insert into public.favorites (menu_id) values ('demo-s-latte');
  assert (select count(*) from public.favorites) = 1, 'A must be able to save its own favorite';
  update public.profiles set display_name='RLS A updated' where id=auth.uid();
  assert (select display_name from public.profiles where id=auth.uid()) = 'RLS A updated', 'Own profile update failed';
  update public.profiles set display_name='unauthorized' where id='f0000000-0000-4000-8000-000000000002';
  get diagnostics changed = row_count;
  assert changed = 0, 'A must not update B profile';
  delete from public.favorites where user_id='f0000000-0000-4000-8000-000000000002';
  get diagnostics changed = row_count;
  assert changed = 0, 'A must not delete B favorites';
  begin
    insert into public.favorites (user_id, menu_id) values ('f0000000-0000-4000-8000-000000000002', 'demo-s-latte');
    raise exception 'A incorrectly inserted for B';
  exception when insufficient_privilege then null;
  end;
  begin
    update public.profiles set id='f0000000-0000-4000-8000-000000000002' where id=auth.uid();
    raise exception 'Profile owner column incorrectly writable';
  exception when insufficient_privilege then null;
  end;
  delete from public.favorites where user_id=auth.uid() and menu_id='demo-s-latte';
  assert (select count(*) from public.favorites) = 0, 'Own favorite delete failed';
end;
$$;

select set_config('request.jwt.claim.sub', 'f0000000-0000-4000-8000-000000000002', true);
select set_config('request.jwt.claims', '{"sub":"f0000000-0000-4000-8000-000000000002","role":"authenticated"}', true);
do $$
begin
  assert (select count(*) from public.profiles) = 1, 'B must see only its own profile';
  assert (select display_name from public.profiles) = 'RLS B', 'B profile was changed by A';
  assert (select count(*) from public.favorites) = 1, 'B favorite must survive A deletion attempt';
end;
$$;

reset role;
set local role anon;
do $$
begin
  begin
    perform 1 from public.profiles;
    raise exception 'Anonymous profile access incorrectly allowed';
  exception when insufficient_privilege then null;
  end;
  begin
    perform 1 from public.favorites;
    raise exception 'Anonymous favorite access incorrectly allowed';
  exception when insufficient_privilege then null;
  end;
end;
$$;
reset role;
rollback;

select
  'PASS: own access, cross-user isolation, protected owner column, anonymous denial' as result,
  not exists (select 1 from auth.users where id in ('f0000000-0000-4000-8000-000000000001', 'f0000000-0000-4000-8000-000000000002')) as test_users_rolled_back,
  not exists (select 1 from public.profiles where id in ('f0000000-0000-4000-8000-000000000001', 'f0000000-0000-4000-8000-000000000002')) as test_profiles_rolled_back;
