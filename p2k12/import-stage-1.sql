DROP SCHEMA IF EXISTS p2k12 CASCADE;
CREATE SCHEMA p2k12;

CREATE TABLE p2k12.accounts (
  id          INTEGER,
  name        TEXT,
  type        TEXT,
  last_billed TIMESTAMPTZ
);

CREATE TABLE p2k12.auth (
  account INTEGER,
  realm   TEXT,
  data    TEXT
);

CREATE TABLE p2k12.members (
  id           INTEGER,
  date         TIMESTAMPTZ,
  full_name    TEXT,
  email        TEXT,
  account      INTEGER,
  organization TEXT,
  price        NUMERIC(8, 0),
  recurrence   TEXT,
  flag         TEXT
);

CREATE TABLE p2k12.checkins (
  id      INTEGER     NOT NULL,
  account INTEGER     NOT NULL,
  date    TIMESTAMPTZ NOT NULL,
  type    TEXT        NOT NULL
);

CREATE TABLE p2k12.stripe_payment (
  invoice_id TEXT          NOT NULL,
  account    INTEGER       NOT NULL,
  start_date DATE          NOT NULL,
  end_date   DATE          NOT NULL,
  price      NUMERIC(8, 2) NOT NULL,
  paid_date  DATE
);

CREATE TABLE p2k12.stripe_customer (
  account INTEGER NOT NULL,
  id      TEXT
);

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
    m.flag = 'm_office' AS office_user
  FROM p2k12.members m
  ORDER BY m.account, m.id DESC;

DROP VIEW IF EXISTS p2k12.duplicate_emails;
CREATE VIEW p2k12.duplicate_emails AS
  SELECT
    email,
    array_agg(id)      AS ids,
    array_agg(account) AS account_ids,
    count(email)       AS count
  FROM p2k12.active_members
  GROUP BY email
  HAVING count(email) > 1
  ORDER BY email;

DROP VIEW IF EXISTS p2k12.first_checkin;
CREATE VIEW p2k12.checkin_stats AS
  SELECT
    account,
    min(checkins.date) first_date,
    max(checkins.date) latest_date
  FROM p2k12.checkins
  GROUP BY account;

CREATE OR REPLACE VIEW p2k12.export AS
  SELECT
    m.account     AS account_id,
    fc.first_date AS created_at,
    fc.first_date AS updated_at,
    a.name        AS username,
    m.email       AS email,
    m.full_name   AS name,
    m.price       AS price
  FROM p2k12.active_members m
    LEFT OUTER JOIN p2k12.accounts a ON m.account = a.id
    LEFT OUTER JOIN p2k12.checkin_stats fc ON a.id = fc.account
  WHERE a.type = 'user'
  ORDER BY account_id ASC;
