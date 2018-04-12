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

\COPY p2k12.accounts FROM 'p2k12/p2k12_accounts.csv' WITH CSV HEADER
\COPY p2k12.auth FROM 'p2k12/p2k12_auth.csv' WITH CSV HEADER
\COPY p2k12.members FROM 'p2k12/p2k12_members.csv' WITH CSV HEADER
\COPY p2k12.checkins FROM 'p2k12/p2k12_checkins.csv' WITH CSV HEADER
\COPY p2k12.stripe_customer FROM 'p2k12/p2k12_stripe_customer.csv' WITH CSV HEADER
\COPY p2k12.stripe_payment FROM 'p2k12/p2k12_stripe_payment.csv' WITH CSV HEADER

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

CREATE VIEW p2k12.duplicate_emails AS
  SELECT email
  FROM p2k12.active_members
  GROUP BY email
  HAVING count(email) > 1
  ORDER BY email;

CREATE VIEW p2k12.first_checkin AS
  SELECT
    account,
    min(checkins.date) date
  FROM p2k12.checkins
  GROUP BY account;

CREATE VIEW p2k12.export AS
  SELECT
    m.account   AS account_id,
    fc.date     AS created_at,
    fc.date     AS updated_at,
    a.name      AS username,
    m.email     AS email,
    m.full_name AS name,
    m.price     AS price
  FROM p2k12.active_members m
    LEFT OUTER JOIN p2k12.accounts a ON m.account = a.id
    LEFT OUTER JOIN p2k12.first_checkin fc ON a.id = fc.account
  WHERE TRUE
        AND a.type = 'user'
        AND m.email NOT IN (SELECT email
                            FROM p2k12.duplicate_emails)
  ORDER BY account_id ASC;

SELECT *
FROM p2k12.members
WHERE email = 'anders@andersand.net';

DELETE FROM public.company_employee_version;
DELETE FROM public.company_employee;
DELETE FROM public.company_version;
DELETE FROM public.company;
DELETE FROM public.circle_member_version;
DELETE FROM public.circle_member;
DELETE FROM public.circle_version;
DELETE FROM public.circle;
DELETE FROM public.account_version;
TRUNCATE public.account_version;
TRUNCATE public.account CASCADE;

-- TODO: reset all sequences to 1?
SELECT setval('id_seq', 100000);
SELECT setval('transaction_id_seq', 100000);

INSERT INTO public.account (created_at, updated_at, username, email, system)
VALUES (current_timestamp, current_timestamp, 'system', 'root@bitraf.no', TRUE);

-- TODO: import accounts without auth records
-- TODO: p2k12 user.price -> p2k16 membership.fee
INSERT INTO public.account (membership_number, created_at, updated_at, username, email, name)
  SELECT
    account_id,
    coalesce(created_at, now()),
    coalesce(updated_at, now()),
    username,
    email,
    name
  FROM p2k12.export
  ORDER BY account_id;

DELETE FROM stripe_customer;
INSERT INTO stripe_customer (created_at, created_by, updated_at, updated_by, stripe_id)
  SELECT
    current_timestamp AS created_at,
    a.id              AS created_by,
    current_timestamp AS created_at,
    a.id              AS updated_by,
    sc.id             AS stripe_id
  FROM p2k12.stripe_customer sc
    LEFT OUTER JOIN public.account a ON a.membership_number = sc.account
  ORDER BY a.id;

-- Update passwords
UPDATE public.account a
SET password = (SELECT data
                FROM p2k12.auth auth
                WHERE a.membership_number = auth.account AND auth.realm = 'door');

DO $$
DECLARE
  system_id        BIGINT := (SELECT id
                              FROM account
                              WHERE username = 'system');
  trygvis_id       BIGINT := (SELECT id
                              FROM account
                              WHERE username = 'trygvis');
  despot_id        BIGINT;
  door_id          BIGINT;
  door_admin_id    BIGINT;
  p2k12_company_id BIGINT;
BEGIN

  INSERT INTO circle (created_at, created_by, updated_at, updated_by, name, description, management_style) VALUES
    (now(), system_id, now(), system_id, 'despot', 'Despot', 'SELF_ADMIN')
  RETURNING id
    INTO despot_id;

  INSERT INTO circle_member (created_at, created_by, updated_at, updated_by, account, circle) VALUES
    (now(), system_id, now(), system_id, trygvis_id, despot_id);

  INSERT INTO circle (created_at, created_by, updated_at, updated_by, name, description, management_style) VALUES
    (now(), system_id, now(), system_id, 'door-admin', 'Door access admins', 'SELF_ADMIN')
  RETURNING id
    INTO door_admin_id;

  INSERT INTO circle_member (created_at, created_by, updated_at, updated_by, account, circle) VALUES
    (now(), system_id, now(), system_id, trygvis_id, door_admin_id);

  INSERT INTO circle (created_at, created_by, updated_at, updated_by, name, description, management_style, admin_circle)
  VALUES
    (now(), system_id, now(), system_id, 'door', 'Door access', 'ADMIN_CIRCLE', door_admin_id)
  RETURNING id
    INTO door_id;

  INSERT INTO circle_member (created_at, created_by, updated_at, updated_by, account, circle)
    WITH paying AS (
        SELECT
          am.account,
          0 < am.price AS paying
        FROM p2k12.active_members am
    )
    SELECT
      now()     AS created_at,
      system_id AS created_by,
      now()     AS updated_at,
      system_id AS updated_by,
      a.id      AS account,
      door_id   AS circle
    FROM public.account a
      INNER JOIN paying p ON a.membership_number = p.account
    WHERE p.paying
    ORDER BY a.id;

  INSERT INTO company (created_at, created_by, updated_at, updated_by, name, active, contact)
  VALUES (now(), system_id, now(), system_id, 'P2k12 Office Users', TRUE, system_id)
  RETURNING id
    INTO p2k12_company_id;

  INSERT INTO company_employee (created_at, created_by, updated_at, updated_by, company, account)
    SELECT
      now()     AS created_at,
      system_id AS created_by,
      now()     AS updated_at,
      system_id AS updated_by,
      p2k12_company_id,
      a.id      AS account
    FROM public.account a
      INNER JOIN p2k12.accounts ON a.membership_number = p2k12.accounts.id
      INNER JOIN p2k12.active_members am ON am.account = a.id
    WHERE am.office_user
    ORDER BY a.id;
END;
$$;
