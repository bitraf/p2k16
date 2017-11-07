DROP TABLE IF EXISTS company_version;
DROP TABLE IF EXISTS company;

CREATE TABLE company
(
  id         BIGSERIAL                 NOT NULL,

  created_at TIMESTAMP                 NOT NULL,
  created_by BIGINT                    NOT NULL REFERENCES account,
  updated_at TIMESTAMP                 NOT NULL,
  updated_by BIGINT                    NOT NULL REFERENCES account,

  name       VARCHAR(100)              NOT NULL UNIQUE,
  active     BOOLEAN                   NOT NULL,
  contact    BIGINT REFERENCES account NOT NULL,

  PRIMARY KEY (id)
);
GRANT ALL ON company TO "p2k16-web";
GRANT ALL ON company_id_seq TO "p2k16-web";

CREATE TABLE company_version
(
  transaction_id     BIGINT       NOT NULL REFERENCES transaction,
  end_transaction_id BIGINT       NULL REFERENCES transaction,
  operation_type     INT          NOT NULL,

  id                 BIGSERIAL    NOT NULL,

  created_at         TIMESTAMP    NOT NULL,
  created_by         BIGINT       NOT NULL,
  updated_at         TIMESTAMP    NOT NULL,
  updated_by         BIGINT       NOT NULL,

  name               VARCHAR(100) NOT NULL,
  active             BOOLEAN      NOT NULL,
  contact            BIGINT       NOT NULL
);
GRANT INSERT, UPDATE ON company_version TO "p2k16-web";
GRANT ALL ON company_version TO "p2k16-web";
