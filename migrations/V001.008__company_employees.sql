DROP TABLE IF EXISTS company_employee_version;
DROP TABLE IF EXISTS company_employee;

CREATE TABLE company_employee
(
  id         BIGSERIAL                 NOT NULL,

  created_at TIMESTAMP                 NOT NULL,
  created_by BIGINT                    NOT NULL REFERENCES account,
  updated_at TIMESTAMP                 NOT NULL,
  updated_by BIGINT                    NOT NULL REFERENCES account,

  company    BIGINT REFERENCES company NOT NULL,
  account    BIGINT REFERENCES account NOT NULL,

  PRIMARY KEY (id),
  UNIQUE (company, account)
);
GRANT ALL ON company_employee TO "p2k16-web";
GRANT ALL ON company_employee_id_seq TO "p2k16-web";

CREATE TABLE company_employee_version
(
  transaction_id     BIGINT    NOT NULL REFERENCES transaction,
  end_transaction_id BIGINT REFERENCES transaction,
  operation_type     INT       NOT NULL,

  id                 BIGINT    NOT NULL,

  created_at         TIMESTAMP NOT NULL,
  created_by         BIGINT    NOT NULL,
  updated_at         TIMESTAMP NOT NULL,
  updated_by         BIGINT    NOT NULL,

  company            BIGINT    NOT NULL,
  account            BIGINT    NOT NULL
);
GRANT INSERT, UPDATE ON company_employee_version TO "p2k16-web";
GRANT ALL ON company_employee_version TO "p2k16-web";
