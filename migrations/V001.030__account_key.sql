/*
Template migration.
*/

DROP TABLE IF EXISTS account_key_version;
DROP TABLE IF EXISTS account_key;

CREATE TABLE account_key (
  id         BIGINT                   NOT NULL PRIMARY KEY DEFAULT nextval('id_seq'),

  created_at TIMESTAMP WITH TIME ZONE NOT NULL,
  created_by BIGINT                   NOT NULL REFERENCES account,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
  updated_by BIGINT                   NOT NULL REFERENCES account,

  account_id BIGINT                   NOT NULL REFERENCES account,
  comment    TEXT,
  public_key TEXT                     NOT NULL,
  key_type   VARCHAR(50)              NOT NULL
);
GRANT ALL ON account_key TO "p2k16-web";

CREATE TABLE account_key_version
(
  transaction_id     BIGINT                   NOT NULL REFERENCES transaction,
  end_transaction_id BIGINT REFERENCES transaction,
  operation_type     INT                      NOT NULL,

  id                 BIGINT                   NOT NULL,

  created_at         TIMESTAMP WITH TIME ZONE NOT NULL,
  created_by         BIGINT                   NOT NULL,
  updated_at         TIMESTAMP WITH TIME ZONE NOT NULL,
  updated_by         BIGINT                   NOT NULL,

  account_id BIGINT,
  comment    TEXT,
  public_key TEXT,
  key_type   VARCHAR(50)
);
GRANT INSERT, UPDATE ON account_key_version TO "p2k16-web";
GRANT ALL ON account_key_version TO "p2k16-web";

