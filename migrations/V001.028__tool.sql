/*
Template migration.
*/

DROP TABLE IF EXISTS tool_description_version;
DROP TABLE IF EXISTS tool_description;

CREATE TABLE tool_description (
  id         BIGINT                   NOT NULL PRIMARY KEY DEFAULT nextval('id_seq'),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL,
  created_by BIGINT                   NOT NULL REFERENCES account,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
  updated_by BIGINT                   NOT NULL REFERENCES account,

  name       VARCHAR(50) NOT NULL,
  description VARCHAR(1000),
);
GRANT ALL ON tool_description TO "p2k16-web";

CREATE TABLE tool_description_version
(
  transaction_id     BIGINT                   NOT NULL REFERENCES transaction,
  end_transaction_id BIGINT REFERENCES transaction,
  operation_type     INT                      NOT NULL,

  id                 BIGINT                   NOT NULL,

  created_at         TIMESTAMP WITH TIME ZONE NOT NULL,
  created_by         BIGINT                   NOT NULL,
  updated_at         TIMESTAMP WITH TIME ZONE NOT NULL,
  updated_by         BIGINT                   NOT NULL,

  name       VARCHAR(50) NOT NULL,
  description VARCHAR(1000),
);
GRANT INSERT, UPDATE ON tool_description_version TO "p2k16-web";
GRANT ALL ON tool_description_version TO "p2k16-web";
