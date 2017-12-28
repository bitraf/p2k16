DROP SCHEMA IF EXISTS p2k12 CASCADE;
CREATE SCHEMA p2k12;

CREATE TABLE p2k12.accounts (
  id          BIGINT,
  name        TEXT,
  type        TEXT,
  last_billed TEXT
);

CREATE TABLE p2k12.auth (
  account BIGINT,
  realm   TEXT,
  data    TEXT
);

CREATE TABLE p2k12.members (
  id           BIGINT,
  date         TEXT,
  full_name    TEXT,
  email        TEXT,
  account      BIGINT,
  organization TEXT,
  price        TEXT,
  recurrence   TEXT,
  flag         TEXT
);

CREATE TABLE p2k12.checkins (
  id      BIGINT    NOT NULL,
  account BIGINT    NOT NULL,
  date    TIMESTAMP NOT NULL,
  type    TEXT      NOT NULL
);

\copy p2k12.accounts from 'p2k12/p2k12_accounts.csv' with csv header
\copy p2k12.auth from 'p2k12/p2k12_auth.csv' with csv header
\copy p2k12.members from 'p2k12/p2k12_members.csv' with csv header
\copy p2k12.checkins from 'p2k12/p2k12_checkins.csv' with csv header

ALTER TABLE p2k12.accounts
  ADD CONSTRAINT accounts__id_uq UNIQUE (id);

ALTER TABLE p2k12.auth
  ADD CONSTRAINT account_fk FOREIGN KEY (account) REFERENCES p2k12.accounts (id);

ALTER TABLE p2k12.members
  ADD CONSTRAINT members__id_uq UNIQUE (id),
  ADD CONSTRAINT account_fk FOREIGN KEY (account) REFERENCES p2k12.accounts (id);

ALTER TABLE p2k12.checkins
  ADD CONSTRAINT checkins__id_uq UNIQUE (id),
  ADD CONSTRAINT account_fk FOREIGN KEY (account) REFERENCES p2k12.accounts (id);

CREATE VIEW p2k12.active_members AS
  SELECT DISTINCT ON (m.account)
    m.id,
    m.date,
    m.full_name,
    m.email,
    m.price,
    m.recurrence,
    m.account,
    m.organization,
    m.flag
  FROM p2k12.members m
  ORDER BY m.account, m.id DESC;

CREATE VIEW p2k12.duplicate_emails AS
  SELECT email
  FROM p2k12.active_members
  GROUP BY email
  HAVING count(email) > 1
  ORDER BY email;

DELETE FROM public.circle_member_version;
DELETE FROM public.circle_member;
DELETE FROM public.circle_version;
DELETE FROM public.circle;
DELETE FROM public.account_version;
DELETE FROM public.account;

INSERT INTO public.account (id, created_at, updated_at, username, email, password, name, phone)
  SELECT *
  FROM (
         WITH
             first_checkin AS (SELECT
                                 account,
                                 min(checkins.date) date
                               FROM p2k12.checkins
                               GROUP BY account)
         SELECT
           m.account :: BIGINT AS id,
           fc.date             AS created_at,
           fc.date             AS updated_at,
           a.name              AS username,
           m.email             AS email,
           auth.data           AS password,
           m.full_name         AS name,
           m.price             AS price
         --     m.recurrence,
         FROM p2k12.active_members m
           INNER JOIN p2k12.accounts a ON m.account = a.id
           INNER JOIN p2k12.auth auth ON a.id = auth.account
           INNER JOIN first_checkin fc ON fc.account = m.account
         WHERE 1 = 1
               AND auth.realm = 'door'
               AND a.type = 'user'
               -- TODO: there shouldn't be any duplicate email addresses
               AND m.email NOT IN (SELECT email
                                   FROM p2k12.duplicate_emails)
         ORDER BY id ASC
       ) AS account
  ORDER BY account.username;
SELECT setval('account_id_seq', (SELECT max(id) + 1
                                 FROM account));
DO $$
DECLARE
  trygvis_id BIGINT;
  admins_id  BIGINT;
  door_id    BIGINT;
  now        TIMESTAMP := (SELECT current_timestamp);
BEGIN

  SELECT id
  FROM account
  WHERE username = 'trygvis'
  INTO trygvis_id;

  INSERT INTO circle (created_at, created_by, updated_at, updated_by, name, description) VALUES
    (now, trygvis_id, now, trygvis_id, 'admins', 'Admin')
  RETURNING id
    INTO admins_id;

  INSERT INTO circle (created_at, created_by, updated_at, updated_by, name, description) VALUES
    (now, trygvis_id, now, trygvis_id, 'door', 'Door access')
  RETURNING id
    INTO door_id;

  INSERT INTO circle_member (created_at, created_by, updated_at, updated_by, account, circle) VALUES
    (now, trygvis_id, now, trygvis_id, trygvis_id, admins_id);

  -- TODO: insert all members with valid memberships into the door group
  INSERT INTO circle_member (created_at, created_by, updated_at, updated_by, account, circle) VALUES
    (now, trygvis_id, now, trygvis_id, trygvis_id, door_id);
END;
$$;
