-- Fix up some bad p2k12 data

DROP TABLE IF EXISTS p2k12.bad_accounts;
CREATE TABLE p2k12.bad_accounts (
  account BIGINT,
  name    VARCHAR
);
INSERT INTO p2k12.bad_accounts (name) VALUES
  ('jon'),
  ('w0ni'),
  ('helenwe'),
  ('Mortengg'),
  ('testaaa'),
  ('josteinvv'),
  ('nailimm'),
  ('phelsethh'),
  ('susejsutsirkk'),
  ('test'),
  ('hsrths'),
  ('sijbren'),
  ('Bek'),
  ('hall'),
  ('davenn');

UPDATE p2k12.bad_accounts ba
SET account = (SELECT id
               FROM p2k12.accounts
               WHERE name = ba.name);

-- SELECT *
-- FROM p2k12.bad_accounts
-- WHERE account IS NULL;

ALTER TABLE p2k12.bad_accounts
  ALTER COLUMN account SET NOT NULL;

DELETE FROM p2k12.auth
WHERE account IN (SELECT account
                  FROM p2k12.bad_accounts);

DELETE FROM p2k12.members
WHERE account IN (SELECT account
                  FROM p2k12.bad_accounts);

DELETE FROM p2k12.checkins
WHERE account IN (SELECT account
                  FROM p2k12.bad_accounts);

DELETE FROM p2k12.accounts
WHERE id IN (SELECT account
             FROM p2k12.bad_accounts);


SELECT
  *,
  (SELECT array_agg(name)
   FROM p2k12.accounts
   WHERE id = account)
FROM p2k12.members
WHERE email IN (SELECT email
                FROM p2k12.duplicate_emails)
ORDER BY id ASC;

SELECT
  m.account      AS account_id,
  fc.first_date  AS created_at,
  fc.first_date  AS updated_at,
  fc.latest_date AS last_date,
  a.name         AS username,
  m.email        AS email,
  m.full_name    AS name,
  m.price        AS price
FROM p2k12.active_members m
  LEFT OUTER JOIN p2k12.accounts a ON m.account = a.id
  LEFT OUTER JOIN p2k12.checkin_stats fc ON a.id = fc.account
WHERE a.type = 'user'
      AND m.email IN (SELECT email
                      FROM p2k12.duplicate_emails)
ORDER BY email, last_date ASC;

