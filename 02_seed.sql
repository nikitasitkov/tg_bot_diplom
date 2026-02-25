-- 02_seed.sql
-- Заполняем только общие слова: owner_user_id = NULL

INSERT INTO word (en, ru, owner_user_id) VALUES
('I', 'Я', NULL),
('You', 'Ты', NULL),
('He', 'Он', NULL),
('She', 'Она', NULL),
('We', 'Мы', NULL),
('They', 'Они', NULL),
('Red', 'Красный', NULL),
('Green', 'Зелёный', NULL),
('Blue', 'Синий', NULL),
('White', 'Белый', NULL)
ON CONFLICT DO NOTHING;