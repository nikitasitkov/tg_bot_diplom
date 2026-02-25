-- 01_schema.sql

CREATE TABLE IF NOT EXISTS tg_user (
    id           BIGSERIAL PRIMARY KEY,
    tg_id        BIGINT UNIQUE NOT NULL,
    username     TEXT,
    first_name   TEXT,
    created_at   TIMESTAMP DEFAULT now()
);

-- word: общие слова имеют owner_user_id = NULL
-- пользовательские слова имеют owner_user_id = tg_user.id
CREATE TABLE IF NOT EXISTS word (
    id            BIGSERIAL PRIMARY KEY,
    en            TEXT NOT NULL,
    ru            TEXT NOT NULL,
    owner_user_id BIGINT REFERENCES tg_user(id) ON DELETE CASCADE,
    created_at    TIMESTAMP DEFAULT now(),
    CONSTRAINT uq_common_word UNIQUE (en, ru, owner_user_id)
);

-- персональное удаление общих слов
-- пользователь скрывает слово из общего словаря
CREATE TABLE IF NOT EXISTS user_hidden_word (
    user_id BIGINT NOT NULL REFERENCES tg_user(id) ON DELETE CASCADE,
    word_id BIGINT NOT NULL REFERENCES word(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (user_id, word_id)
);

-- Индексы для быстрого поиска и выборки
CREATE INDEX IF NOT EXISTS idx_word_owner ON word(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_word_en ON word(en);
CREATE INDEX IF NOT EXISTS idx_word_ru ON word(ru);
CREATE INDEX IF NOT EXISTS idx_hidden_user ON user_hidden_word(user_id);