-- SQLite 설계 예시. 앱에서 실행하지 않음. DBMS·인증 방식 미확정.
PRAGMA foreign_keys = ON;
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    password_hash TEXT,
    display_name TEXT NOT NULL CHECK (length(trim(display_name)) BETWEEN 1 AND 24),
    created_at TEXT NOT NULL
);
CREATE TABLE sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX sessions_user_id_idx ON sessions(user_id);
CREATE INDEX sessions_expires_at_idx ON sessions(expires_at);
-- JSON 단계: menu_id 존재 여부는 서버 검증. B 전환 시 FK 마이그레이션 추가.
CREATE TABLE favorites (
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    menu_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (user_id, menu_id)
);
