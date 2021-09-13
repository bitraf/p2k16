DROP TABLE IF EXISTS q_message;

DROP SEQUENCE IF EXISTS q_id_seq;

CREATE SEQUENCE q_id_seq START 1000000;

CREATE TABLE q_message
(
  id           BIGINT                            DEFAULT (NEXTVAL('q_id_seq')),
  created_at   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  processed_at TIMESTAMP WITH TIME ZONE,

  queue        VARCHAR(100)             NOT NULL,
  entity_id    BIGINT                   NOT NULL,
  PRIMARY KEY (id)
);

GRANT INSERT, SELECT, UPDATE ON q_message TO "p2k16-web";
GRANT USAGE ON q_id_seq TO "p2k16-web";
