DROP TABLE IF EXISTS event;

CREATE TABLE event (
  id         BIGSERIAL                NOT NULL PRIMARY KEY,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL,
  created_by BIGINT                   NOT NULL REFERENCES account,

  domain     VARCHAR                  NOT NULL,

  int1       INTEGER,
  int2       INTEGER,
  int3       INTEGER,
  int4       INTEGER,
  int5       INTEGER,

  text1      VARCHAR,
  text2      VARCHAR,
  text3      VARCHAR,
  text4      VARCHAR,
  text5      VARCHAR
);
GRANT ALL ON event TO "p2k16-web";
GRANT ALL ON event_id_seq TO "p2k16-web";

DROP TABLE IF EXISTS audit_record_version;
DROP TABLE IF EXISTS audit_record;
