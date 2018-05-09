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
TRUNCATE p2k16.public.transaction CASCADE;

SELECT setval('id_seq', 100000);
SELECT setval('transaction_id_seq', 100000);

INSERT INTO public.account (created_at, updated_at, username, email, system)
VALUES (current_timestamp, current_timestamp, 'system', 'root@bitraf.no', TRUE);

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

DO $$
DECLARE
  p2k12_count INT;
  p2k16_count INT;
BEGIN
  DELETE FROM stripe_payment;
  INSERT INTO stripe_payment (created_at, created_by, updated_at, updated_by, stripe_id, start_date, end_date, amount, payment_date)
    SELECT
      coalesce(paid_date, (end_date + '1 day' :: INTERVAL) :: DATE) AS created_at,
      account.id                                                    AS created_by,

      coalesce(paid_date, (end_date + '1 day' :: INTERVAL) :: DATE) AS updated_at,
      account.id                                                    AS updated_by,

      invoice_id                                                    AS stripe_id,
      start_date,
      end_date,
      price                                                         AS amount,
      coalesce(paid_date, (end_date + '1 day' :: INTERVAL) :: DATE) AS payment_date
    FROM p2k12.stripe_payment
      LEFT OUTER JOIN account ON p2k12.stripe_payment.account = account.membership_number;

  SELECT count(*) AS count
  FROM p2k12.stripe_payment
  INTO p2k12_count;
  SELECT count(*) AS count
  FROM public.stripe_payment
  INTO p2k16_count;

  IF p2k12_count != p2k16_count
  THEN RAISE 'bad data'; END IF;
END;
$$;

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
  p2k12            BIGINT;
  p2k16            BIGINT;
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
      --       INNER JOIN p2k12.active_members am ON am.account = a.id
      LEFT OUTER JOIN p2k12.active_members am ON a.membership_number = am.account
    WHERE am.office_user
    ORDER BY a.id;

  INSERT INTO membership (created_at, created_by, updated_at, updated_by, first_membership, start_membership, fee)
    SELECT
      now()                                  AS created_at,
      (SELECT id
       FROM account
       WHERE membership_number = am.account) AS created_by,
      now()                                  AS updated_at,
      (SELECT id
       FROM account
       WHERE membership_number = am.account) AS updated_by,
      (SELECT min(date)
       FROM p2k12.members
       WHERE account = am.account)           AS first_membership,
      '2000-01-01' :: DATE                   AS start_membership,
      price                                  AS fee
    FROM p2k12.active_members am;

  SELECT count(*)
  FROM p2k12.active_members
  WHERE office_user
  INTO p2k12;

  SELECT count(*)
  FROM company_employee
  WHERE company_employee.company = p2k12_company_id
  INTO p2k16;

  IF p2k12 != p2k16
  THEN
    RAISE 'Bad number of office users migrated, p2k12: %, p2k16: %', p2k12, p2k16;
  END IF;

END;
$$;
