/* 한정원 담당. Supabase Auth + profiles/favorites. 메뉴 데이터는 별도 계약을 유지. */
(function () {
  "use strict";

  const config = window.CafeConfig || {};
  let client = null;
  let rawUser = null;
  let profile = null;
  let favoriteIds = new Set();
  let epoch = 0;
  let initialized = false;
  let setupError = null;
  let profileError = null;
  let favoriteError = null;
  let recovery = false;
  const recoveryKey = "csm.supabase.recovery.v1";
  const pendingFavorites = new Set();

  function emit(name) { window.dispatchEvent(new CustomEvent(name)); }
  function fail(message, code) {
    const error = new Error(message);
    error.code = code;
    return error;
  }
  function friendly(error) {
    const code = error && error.code;
    if (code === "invalid_credentials") return fail("이메일 또는 비밀번호를 확인해 주세요.", code);
    if (code === "email_not_confirmed") return fail("이메일 인증 후 로그인해 주세요. 인증 메일을 다시 받을 수도 있어요.", code);
    if (code === "over_email_send_rate_limit" || code === "over_request_rate_limit" || (error && error.status === 429)) return fail("요청이 많아요. 잠시 후 다시 시도해 주세요.", code);
    if (code === "weak_password") return fail("비밀번호가 서비스의 보안 기준에 맞지 않아요. 더 긴 비밀번호를 사용해 주세요.", code);
    if (["PGRST205", "42P01", "42501"].includes(code)) return fail("저장소 연결을 확인해야 합니다. 잠시 후 다시 시도해 주세요.", "DATABASE_SETUP_REQUIRED");
    return fail("요청을 완료하지 못했어요. 연결 상태를 확인하고 다시 시도해 주세요.", code || "REQUEST_FAILED");
  }
  function validateConfig() {
    if (!config.supabaseUrl || !config.supabasePublishableKey) throw fail("로그인 연결을 준비 중입니다. 설정 후 이용할 수 있어요.", "CONFIG_REQUIRED");
    const url = new URL(config.supabaseUrl);
    if (url.username || url.password || url.search || url.hash) throw fail("Supabase 주소 설정을 확인해 주세요.", "CONFIG_INVALID");
    if (url.protocol !== "https:" && !(url.protocol === "http:" && ["localhost", "127.0.0.1"].includes(url.hostname))) throw fail("Supabase 주소 설정을 확인해 주세요.", "CONFIG_INVALID");
    const key = config.supabasePublishableKey;
    if (typeof key !== "string" || key.startsWith("sb_secret_")) throw fail("브라우저용 공개 키 설정을 확인해 주세요.", "CONFIG_INVALID");
    if (!key.startsWith("sb_publishable_")) {
      try {
        const encoded = key.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
        if (JSON.parse(atob(encoded)).role !== "anon") throw new Error("wrong role");
      } catch (_) { throw fail("publishable 또는 anon 공개 키만 사용할 수 있습니다.", "CONFIG_INVALID"); }
    }
  }
  function rememberRecovery(value) {
    recovery = value;
    try {
      if (value && rawUser) sessionStorage.setItem(recoveryKey, rawUser.id);
      else sessionStorage.removeItem(recoveryKey);
    } catch (_) { /* 복구 상태 저장이 막히면 현재 페이지에서만 처리한다. */ }
  }
  function assignSession(session, event) {
    const next = session && session.user ? session.user : null;
    if (rawUser && next && rawUser.id !== next.id) rememberRecovery(false);
    if (!next || !rawUser || next.id !== rawUser.id) {
      profile = null;
      profileError = null;
      favoriteError = null;
      favoriteIds = new Set();
    }
    rawUser = next;
    epoch += 1;
    if (!next) rememberRecovery(false);
    else if (event === "PASSWORD_RECOVERY") rememberRecovery(true);
    return epoch;
  }
  function user() {
    if (!rawUser) return null;
    return {
      id: rawUser.id,
      email: rawUser.email || "",
      displayName: profile && profile.display_name || rawUser.user_metadata && rawUser.user_metadata.display_name || "카페 친구",
      isDemo: false
    };
  }
  function checkOwner(owner, revision) {
    if (!rawUser || rawUser.id !== owner || epoch !== revision) throw fail("로그인 상태가 변경됐어요. 다시 시도해 주세요.", "SESSION_CHANGED");
  }
  async function loadFavorites() {
    if (!rawUser) return [];
    const owner = rawUser.id;
    const revision = epoch;
    const result = await client.from("favorites").select("menu_id").eq("user_id", owner).order("created_at", { ascending: false });
    checkOwner(owner, revision);
    if (result.error) { favoriteError = friendly(result.error); throw favoriteError; }
    favoriteIds = new Set((result.data || []).map(item => item.menu_id));
    favoriteError = null;
    return Array.from(favoriteIds);
  }
  async function hydrate(revision) {
    if (!rawUser || revision !== epoch) return;
    const owner = rawUser.id;
    const result = await client.from("profiles").select("id, display_name").eq("id", owner).maybeSingle();
    if (revision !== epoch || !rawUser || rawUser.id !== owner) return;
    profileError = result.error ? friendly(result.error) : !result.data ? fail("프로필 연결을 확인해야 합니다.", "PROFILE_MISSING") : null;
    if (result.data) profile = result.data;
    try { await loadFavorites(); }
    catch (error) { if (revision === epoch && error.code !== "SESSION_CHANGED") favoriteError = error; }
  }
  const ready = (async function () {
    try {
      validateConfig();
      if (!window.supabase || !window.supabase.createClient) throw fail("로그인 모듈을 불러오지 못했습니다.", "SDK_UNAVAILABLE");
      client = window.supabase.createClient(config.supabaseUrl, config.supabasePublishableKey, {
        auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true, flowType: "pkce", storageKey: "csm.supabase.auth.v1" }
      });
      client.auth.onAuthStateChange(function (event, session) {
        if (event === "INITIAL_SESSION") return;
        if (event === "TOKEN_REFRESHED" && rawUser && session && session.user.id === rawUser.id) {
          rawUser = session.user;
          return;
        }
        const revision = assignSession(session, event);
        // Auth 콜백 내부에서 Supabase 요청을 await하지 않는다.
        setTimeout(async function () {
          if (revision !== epoch) return;
          try { await hydrate(revision); }
          catch (error) { if (revision === epoch) profileError = friendly(error); }
          if (revision === epoch) { emit("cafe:session-changed"); emit("cafe:favorites-changed"); }
        }, 0);
      });
      const result = await client.auth.getSession();
      if (result.error) throw friendly(result.error);
      const revision = assignSession(result.data.session);
      try { recovery = Boolean(rawUser && sessionStorage.getItem(recoveryKey) === rawUser.id); } catch (_) { /* 현재 상태 유지 */ }
      await hydrate(revision);
    } catch (error) {
      setupError = error.code ? error : friendly(error);
      rawUser = null;
      favoriteIds = new Set();
    } finally {
      initialized = true;
      setTimeout(() => { emit("cafe:auth-ready"); emit("cafe:favorites-changed"); }, 0);
    }
  }());
  async function requireClient(authenticated) {
    await ready;
    if (setupError) throw setupError;
    if (authenticated && !rawUser) throw fail("로그인 후 즐겨찾기를 사용할 수 있어요.", "AUTH_REQUIRED");
    return client;
  }
  function redirectUrl() { return new URL("mypage.html", location.href).href; }
  async function acceptSession(session) {
    if (!session) return null;
    const revision = assignSession(session);
    await hydrate(revision);
    emit("cafe:session-changed");
    emit("cafe:favorites-changed");
    return user();
  }

  window.CafeAuth = {
    ready,
    status: () => ({ initialized, configured: !setupError && Boolean(client), error: setupError && setupError.message, code: setupError && setupError.code, dataError: (profileError || favoriteError) && (profileError || favoriteError).message, recovery }),
    getSession: async () => { await ready; return user(); },
    isFavorite: id => Boolean(rawUser && favoriteIds.has(id)),
    getFavoriteIds: async () => { await requireClient(true); return loadFavorites(); },
    signIn: async function ({ email, password }) {
      const sdk = await requireClient(false);
      const result = await sdk.auth.signInWithPassword({ email: email.trim(), password });
      if (result.error) throw friendly(result.error);
      rememberRecovery(false);
      return acceptSession(result.data.session);
    },
    signUp: async function ({ email, password, displayName }) {
      const sdk = await requireClient(false);
      const name = displayName.trim();
      if (!name || name.length > 24) throw fail("표시 이름은 1~24자로 입력해 주세요.", "INVALID_NAME");
      const result = await sdk.auth.signUp({ email: email.trim(), password, options: { data: { display_name: name }, emailRedirectTo: redirectUrl() } });
      if (result.error) throw friendly(result.error);
      const signedIn = Boolean(result.data.session);
      if (signedIn) await acceptSession(result.data.session);
      return { signedIn };
    },
    signOut: async function () {
      const sdk = await requireClient(false);
      const result = await sdk.auth.signOut({ scope: "local" });
      if (result.error) throw friendly(result.error);
      assignSession(null);
      emit("cafe:session-changed"); emit("cafe:favorites-changed");
    },
    updateProfile: async function (displayName) {
      const sdk = await requireClient(true);
      const name = displayName.trim();
      if (!name || name.length > 24) throw fail("표시 이름은 1~24자로 입력해 주세요.", "INVALID_NAME");
      const owner = rawUser.id, revision = epoch;
      const result = await sdk.from("profiles").update({ display_name: name }).eq("id", owner).select("id, display_name").single();
      checkOwner(owner, revision);
      if (result.error) throw friendly(result.error);
      profile = result.data;
      profileError = null;
      emit("cafe:session-changed");
      return user();
    },
    toggleFavorite: async function (id) {
      const sdk = await requireClient(true);
      if (pendingFavorites.has(id)) throw fail("저장 중입니다. 잠시 기다려 주세요.", "BUSY");
      pendingFavorites.add(id);
      try {
        await loadFavorites();
        const owner = rawUser.id, revision = epoch;
        const saved = favoriteIds.has(id);
        const result = saved ? await sdk.from("favorites").delete().eq("user_id", owner).eq("menu_id", id) : await sdk.from("favorites").insert({ user_id: owner, menu_id: id });
        checkOwner(owner, revision);
        if (result.error && !(result.error.code === "23505" && !saved)) throw friendly(result.error);
        if (saved) favoriteIds.delete(id); else favoriteIds.add(id);
        emit("cafe:favorites-changed");
        return !saved;
      } finally { pendingFavorites.delete(id); }
    },
    resendConfirmation: async function (email) {
      const sdk = await requireClient(false);
      const result = await sdk.auth.resend({ type: "signup", email: email.trim(), options: { emailRedirectTo: redirectUrl() } });
      if (result.error) throw friendly(result.error);
    },
    sendPasswordReset: async function (email) {
      const sdk = await requireClient(false);
      const result = await sdk.auth.resetPasswordForEmail(email.trim(), { redirectTo: redirectUrl() });
      if (result.error) throw friendly(result.error);
    },
    updatePassword: async function (password) {
      const sdk = await requireClient(true);
      if (!recovery) throw fail("비밀번호 재설정 메일의 링크를 먼저 열어 주세요.", "RECOVERY_REQUIRED");
      const result = await sdk.auth.updateUser({ password });
      if (result.error) throw friendly(result.error);
      rememberRecovery(false);
      emit("cafe:session-changed");
    }
  };
}());
