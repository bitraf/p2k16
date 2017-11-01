GRANT USAGE ON SCHEMA "public" TO "p2k16-web";

CREATE TABLE account
(
  id                   SERIAL       NOT NULL PRIMARY KEY,
  username             VARCHAR(50)  NOT NULL UNIQUE,
  email                VARCHAR(120) NOT NULL UNIQUE,
  password             VARCHAR(100),
  name                 VARCHAR(100) UNIQUE,
  phone                VARCHAR(50) UNIQUE,
  reset_token          VARCHAR(50) UNIQUE,
  reset_token_validity TIMESTAMP
);
GRANT ALL ON account TO "p2k16-web";

CREATE TABLE circle
(
  id          SERIAL      NOT NULL PRIMARY KEY,
  name        VARCHAR(50) NOT NULL UNIQUE,
  description VARCHAR(50) NOT NULL UNIQUE
);
GRANT ALL ON circle TO "p2k16-web";

CREATE TABLE circle_member
(
  id         SERIAL  NOT NULL PRIMARY KEY,
  circle_id  INTEGER NOT NULL REFERENCES circle,
  account_id INTEGER NOT NULL REFERENCES account,
  issuer_id  INTEGER NOT NULL REFERENCES account,
  UNIQUE (circle_id, account_id)
);
GRANT ALL ON circle_member TO "p2k16-web";

CREATE TABLE audit_record
(
  id         SERIAL       NOT NULL PRIMARY KEY,
  account_id INTEGER REFERENCES account,
  timestamp  TIMESTAMP    NOT NULL,
  object     VARCHAR(100) NOT NULL,
  action     VARCHAR(100) NOT NULL
);
GRANT ALL ON audit_record TO "p2k16-web";

CREATE TABLE membership
(
  id               SERIAL    NOT NULL PRIMARY KEY,
  account_id       INTEGER   NOT NULL REFERENCES account,
  first_membership TIMESTAMP NOT NULL,
  start_membership TIMESTAMP NOT NULL,
  fee              INTEGER   NOT NULL
);
GRANT ALL ON membership TO "p2k16-web";

CREATE TABLE membership_payment
(
  id            SERIAL        NOT NULL PRIMARY KEY,
  account_id    INTEGER       NOT NULL REFERENCES account,
  membership_id VARCHAR(50)   NOT NULL UNIQUE,
  start_date    TIMESTAMP     NOT NULL,
  end_date      TIMESTAMP     NOT NULL,
  amount        NUMERIC(8, 2) NOT NULL,
  payment_date  TIMESTAMP
);
GRANT ALL ON membership_payment TO "p2k16-web";

DO $$
DECLARE
  admins_id BIGINT;
  door_id   BIGINT;
  super_id  BIGINT;
  foo_id    BIGINT;
BEGIN
  DELETE FROM circle_member;
  DELETE FROM circle;
  DELETE FROM account;

  INSERT INTO circle (name, description) VALUES ('admins', 'Admin')
  RETURNING id
    INTO admins_id;

  INSERT INTO circle (name, description) VALUES ('door', 'Door access')
  RETURNING id
    INTO door_id;

  INSERT INTO account (username, email, name, phone, password) VALUES
    ('super', 'super@example.org', 'Super Account', '01234567',
     '$2b$12$B/kxR5O85fN357.fZNUPoOiNblCj7j2lX3/VLajLvuE42OmqsyUTO')
  RETURNING id
    INTO super_id;
  INSERT INTO account (username, email, name, phone, password) VALUES
    ('foo', 'foo@example.org', 'Foo Bar', '76543210', '$2b$12$o764MV/jh0HnsAtsEz53L.GfbLwCqZ5jTf3aV2yUAFFCaTrzGCcQm')
  RETURNING id
    INTO foo_id;

  INSERT INTO circle_member (account_id, circle_id, issuer_id) VALUES
    (super_id, admins_id, super_id),
    (super_id, door_id, super_id),
    (foo_id, door_id, super_id);
END;
$$;
