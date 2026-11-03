-- Supabase Postgres용. 프로젝트 SQL Editor에서 적용하거나 Supabase CLI로 배포한다.
-- 기존 SQLite 예시(accounts.sql/catalog.sql)를 Supabase에서 실행하지 않는다.
begin;

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null check (char_length(btrim(display_name)) between 1 and 24),
  created_at timestamptz not null default now()
);

create table public.favorites (
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  menu_id text not null check (char_length(menu_id) between 1 and 120),
  created_at timestamptz not null default now(),
  primary key (user_id, menu_id)
);
-- 메뉴는 기존 공통 예시 파일을 사용하므로 현재 menu_id FK는 없다.
-- 메뉴 DB를 도입할 때 안정적인 ID를 유지하며 별도 마이그레이션으로 연결한다.

alter table public.profiles enable row level security;
alter table public.favorites enable row level security;

revoke all on public.profiles from anon, authenticated;
revoke all on public.favorites from anon, authenticated;
grant select on public.profiles to authenticated;
grant update (display_name) on public.profiles to authenticated;
grant select, insert, delete on public.favorites to authenticated;

create policy profiles_read_own on public.profiles
  for select to authenticated using ((select auth.uid()) = id);
create policy profiles_update_own on public.profiles
  for update to authenticated
  using ((select auth.uid()) = id)
  with check ((select auth.uid()) = id);

create policy favorites_read_own on public.favorites
  for select to authenticated using ((select auth.uid()) = user_id);
create policy favorites_insert_own on public.favorites
  for insert to authenticated with check ((select auth.uid()) = user_id);
create policy favorites_delete_own on public.favorites
  for delete to authenticated using ((select auth.uid()) = user_id);

create function public.handle_csm_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id, display_name)
  values (
    new.id,
    coalesce(nullif(left(btrim(new.raw_user_meta_data ->> 'display_name'), 24), ''), '카페 친구')
  );
  return new;
end;
$$;
revoke all on function public.handle_csm_new_user() from public, anon, authenticated;

create trigger csm_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_csm_new_user();

-- 이 프로젝트에 이미 가입한 사용자도 프로필을 갖도록 초기 반영.
insert into public.profiles (id, display_name)
select id, coalesce(nullif(left(btrim(raw_user_meta_data ->> 'display_name'), 24), ''), '카페 친구')
from auth.users
on conflict (id) do nothing;

commit;
