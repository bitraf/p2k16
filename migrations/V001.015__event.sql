ALTER TABLE event
  DROP COLUMN IF EXISTS name;

ALTER TABLE event
  ADD COLUMN name VARCHAR;

UPDATE event
SET name = text1, text1 = text2, text2 = NULL
WHERE domain = 'door' AND text1 = 'open';
