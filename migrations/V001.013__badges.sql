DROP TABLE IF EXISTS account_badge_version;
DROP TABLE IF EXISTS account_badge;
DROP TABLE IF EXISTS badge_description_version;
DROP TABLE IF EXISTS badge_description;

CREATE TABLE badge_description
(
  id                   BIGSERIAL NOT NULL PRIMARY KEY,

  created_at           TIMESTAMP NOT NULL,
  created_by           BIGINT    NOT NULL REFERENCES account,
  updated_at           TIMESTAMP NOT NULL,
  updated_by           BIGINT    NOT NULL REFERENCES account,

  title                VARCHAR   NOT NULL,
  certification_circle BIGINT REFERENCES circle,
  slug                 VARCHAR,
  icon                 VARCHAR,
  color                VARCHAR
);
GRANT ALL ON badge_description TO "p2k16-web";
GRANT ALL ON badge_description_id_seq TO "p2k16-web";

CREATE TABLE badge_description_version
(
  transaction_id       BIGINT    NOT NULL REFERENCES transaction,
  end_transaction_id   BIGINT REFERENCES transaction,
  operation_type       INT       NOT NULL,

  id                   BIGSERIAL NOT NULL,

  created_at           TIMESTAMP NOT NULL,
  created_by           BIGINT    NOT NULL,
  updated_at           TIMESTAMP NOT NULL,
  updated_by           BIGINT    NOT NULL,

  title                VARCHAR,
  certification_circle BIGINT,
  slug                 VARCHAR,
  icon                 VARCHAR,
  color                VARCHAR
);
GRANT INSERT, UPDATE ON badge_description_version TO "p2k16-web";
GRANT ALL ON badge_description_version TO "p2k16-web";

CREATE TABLE account_badge
(
  id                BIGSERIAL NOT NULL PRIMARY KEY,

  created_at        TIMESTAMP NOT NULL,
  created_by        BIGINT    NOT NULL REFERENCES account,
  updated_at        TIMESTAMP NOT NULL,
  updated_by        BIGINT    NOT NULL REFERENCES account,

  account           BIGINT    NOT NULL REFERENCES account,
  badge_description BIGINT    NOT NULL,
  awarded_by        BIGINT REFERENCES account
);
GRANT ALL ON account_badge TO "p2k16-web";
GRANT ALL ON account_badge_id_seq TO "p2k16-web";

CREATE TABLE account_badge_version
(
  transaction_id     BIGINT    NOT NULL REFERENCES transaction,
  end_transaction_id BIGINT REFERENCES transaction,
  operation_type     INT       NOT NULL,

  id                 BIGSERIAL NOT NULL,

  created_at         TIMESTAMP NOT NULL,
  created_by         BIGINT    NOT NULL,
  updated_at         TIMESTAMP NOT NULL,
  updated_by         BIGINT    NOT NULL,

  account            BIGINT    NOT NULL REFERENCES account,
  badge_description  BIGINT    NOT NULL,
  awarded_by         BIGINT
);
GRANT INSERT, UPDATE ON account_badge_version TO "p2k16-web";
GRANT ALL ON account_badge_version TO "p2k16-web";
