import random
from dataclasses import dataclass
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor


@dataclass
class Card:
    word_id: int
    en: str
    ru: str


class DB:
    def __init__(self, dsn: str):
        self.dsn = dsn

    def _conn(self):
        return psycopg2.connect(self.dsn)

    def upsert_user(self, tg_id: int, username: Optional[str], first_name: Optional[str]) -> int:
        """
        Возвращает внутренний user_id (tg_user.id).
        """
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tg_user (tg_id, username, first_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (tg_id)
                DO UPDATE SET username = EXCLUDED.username,
                              first_name = EXCLUDED.first_name
                RETURNING id;
                """,
                (tg_id, username, first_name),
            )
            return cur.fetchone()[0]

    def user_word_count(self, user_id: int) -> int:
        """
        Сколько слов доступно пользователю = общие (кроме скрытых) + пользовательские.
        """
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  (
                    SELECT COUNT(*)
                    FROM word w
                    WHERE w.owner_user_id IS NULL
                      AND NOT EXISTS (
                        SELECT 1 FROM user_hidden_word uh
                        WHERE uh.user_id = %s AND uh.word_id = w.id
                      )
                  )
                  +
                  (
                    SELECT COUNT(*)
                    FROM word w2
                    WHERE w2.owner_user_id = %s
                  ) AS cnt;
                """,
                (user_id, user_id),
            )
            return int(cur.fetchone()[0])

    def _visible_words(self, user_id: int) -> list[Card]:
        """
        Все слова, видимые пользователю.
        """
        with self._conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT w.id AS word_id, w.en, w.ru
                FROM word w
                WHERE
                    (
                        w.owner_user_id IS NULL
                        AND NOT EXISTS (
                            SELECT 1 FROM user_hidden_word uh
                            WHERE uh.user_id = %s AND uh.word_id = w.id
                        )
                    )
                    OR w.owner_user_id = %s
                """,
                (user_id, user_id),
            )
            rows = cur.fetchall()
            return [Card(**r) for r in rows]

    def get_random_card(self, user_id: int) -> Card:
        words = self._visible_words(user_id)
        if len(words) < 4:
            raise RuntimeError("Недостаточно слов для формирования 4 вариантов ответа.")
        return random.choice(words)

    def build_options(self, user_id: int, correct: Card, n: int = 4) -> list[str]:
        """
        4 варианта на английском: correct.en + 3 случайных других.
        """
        words = self._visible_words(user_id)
        pool = [w.en for w in words if w.en != correct.en]
        if len(pool) < (n - 1):
            raise RuntimeError("Недостаточно слов для вариантов.")
        others = random.sample(pool, k=n - 1)
        options = [correct.en] + others
        random.shuffle(options)
        return options

    def add_user_word(self, user_id: int, en: str, ru: str) -> None:
        en = en.strip()
        ru = ru.strip()
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO word (en, ru, owner_user_id)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING;
                """,
                (en, ru, user_id),
            )

    def delete_word_for_user(self, user_id: int, word_id: int) -> str:
        """
        Если слово пользовательское -> удаляем из word.
        Если слово общее -> добавляем в user_hidden_word (персонально скрываем).
        Возвращаем строку-статус для ответа.
        """
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT owner_user_id FROM word WHERE id=%s;", (word_id,))
            row = cur.fetchone()
            if not row:
                return "Слово не найдено."

            owner_user_id = row[0]
            if owner_user_id == user_id:
                cur.execute("DELETE FROM word WHERE id=%s;", (word_id,))
                return "Пользовательское слово удалено."
            if owner_user_id is None:
                cur.execute(
                    """
                    INSERT INTO user_hidden_word (user_id, word_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;
                    """,
                    (user_id, word_id),
                )
                return "Слово скрыто для вас (у других останется)."

            return "Нельзя удалить чужое пользовательское слово."