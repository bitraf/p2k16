DROP TABLE IF EXISTS stripe_customer;
DROP TABLE IF EXISTS stripe_customer_version;

CREATE TABLE stripe_customer
(
  id               BIGSERIAL NOT NULL PRIMARY KEY,

  created_at       TIMESTAMP NOT NULL,
  created_by       BIGINT    NOT NULL REFERENCES account,
  updated_at       TIMESTAMP NOT NULL,
  updated_by       BIGINT    NOT NULL REFERENCES account,

  stripe_id VARCHAR(50) NOT NULL UNIQUE
);
GRANT ALL ON stripe_customer TO "p2k16-web";
GRANT ALL ON stripe_customer_id_seq TO "p2k16-web";

CREATE TABLE stripe_customer_version
(
  transaction_id     BIGINT    NOT NULL REFERENCES transaction,
  end_transaction_id BIGINT REFERENCES transaction,
  operation_type     INT       NOT NULL,

  id                 BIGSERIAL NOT NULL,

  created_at         TIMESTAMP NOT NULL,
  created_by         BIGINT    NOT NULL,
  updated_at         TIMESTAMP NOT NULL,
  updated_by         BIGINT    NOT NULL,

  stripe_id VARCHAR(50) NOT NULL UNIQUE
);
GRANT INSERT, UPDATE ON stripe_customer_version TO "p2k16-web";
GRANT ALL ON stripe_customer_version TO "p2k16-web";
