/*
Template migration.
*/
DROP TABLE IF EXISTS tool_checkout_version;
DROP TABLE IF EXISTS tool_checkout;

DROP TABLE IF EXISTS tool_description_version;
DROP TABLE IF EXISTS tool_description;

CREATE TABLE tool_description (
  id         BIGINT                   NOT NULL PRIMARY KEY DEFAULT nextval('id_seq'),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL,
  created_by BIGINT                   NOT NULL REFERENCES account,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
  updated_by BIGINT                   NOT NULL REFERENCES account,

  name       VARCHAR(50) NOT NULL,
  description TEXT,
  circle     BIGINT                   REFERENCES circle
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
  description TEXT,
  circle      BIGINT
);
GRANT INSERT, UPDATE ON tool_description_version TO "p2k16-web";
GRANT ALL ON tool_description_version TO "p2k16-web";


CREATE TABLE tool_checkout
(
  id         BIGINT                      NOT NULL PRIMARY KEY DEFAULT nextval('id_seq'),
  created_at TIMESTAMP WITH TIME ZONE    NOT NULL,
  created_by BIGINT                      NOT NULL REFERENCES account,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
  updated_by BIGINT                   NOT NULL REFERENCES account,

  tool_description          BIGINT      NOT NULL references tool_description,
  account       BIGINT      NOT NULL references account,
  started       TIMESTAMP WITH TIME ZONE
);

GRANT ALL ON tool_checkout to "p2k16-web";

CREATE TABLE tool_checkout_version
(
  transaction_id     BIGINT                   NOT NULL REFERENCES transaction,
  end_transaction_id BIGINT REFERENCES transaction,
  operation_type     INT                      NOT NULL,

  id                 BIGINT                   NOT NULL,

  created_at         TIMESTAMP WITH TIME ZONE NOT NULL,
  created_by         BIGINT                   NOT NULL,
  updated_at         TIMESTAMP WITH TIME ZONE NOT NULL,
  updated_by         BIGINT                   NOT NULL,

  tool_description          BIGINT    ,
  account       BIGINT      ,
  started       TIMESTAMP WITH TIME ZONE
);

GRANT ALL ON tool_checkout_version TO "p2k16-web";
