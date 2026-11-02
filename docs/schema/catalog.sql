-- 선택 B의 SQLite 설계 예시. 앱에서 실행하지 않음.
PRAGMA foreign_keys = ON;
CREATE TABLE brands (id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE menus (
    id TEXT PRIMARY KEY,
    brand_id TEXT NOT NULL REFERENCES brands(id),
    source_product_id TEXT,
    name TEXT NOT NULL,
    official_is_new INTEGER CHECK (official_is_new IN (0, 1)),
    seasonal INTEGER CHECK (seasonal IN (0, 1)),
    released_at TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    source_url TEXT NOT NULL,
    UNIQUE (brand_id, source_product_id)
);
CREATE INDEX menus_brand_id_idx ON menus(brand_id);
CREATE TABLE menu_servings (
    id TEXT PRIMARY KEY,
    menu_id TEXT NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
    size_label TEXT NOT NULL,
    volume_ml REAL CHECK (volume_ml > 0),
    temperature TEXT NOT NULL CHECK (temperature IN ('HOT', 'ICE', 'OTHER')),
    price_krw INTEGER CHECK (price_krw >= 0),
    sugar_g REAL CHECK (sugar_g >= 0),
    calories_kcal REAL CHECK (calories_kcal >= 0),
    source_url TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    UNIQUE (menu_id, size_label, temperature)
);
CREATE TABLE categories (id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE menu_category_tags (
    menu_id TEXT NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
    category_id TEXT NOT NULL REFERENCES categories(id),
    PRIMARY KEY (menu_id, category_id)
);
-- favorites.menu_id FK 추가는 database.md의 전환 단계 참고.
