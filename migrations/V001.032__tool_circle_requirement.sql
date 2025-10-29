DROP TABLE IF EXISTS tool_circle_requirement_version;
DROP TABLE IF EXISTS tool_circle_requirement;

CREATE TABLE tool_circle_requirement
(
    tool_id   BIGINT REFERENCES tool_description,
    circle_id BIGINT REFERENCES circle,
    PRIMARY KEY (tool_id, circle_id)
);
GRANT ALL ON tool_circle_requirement TO "p2k16-web";

CREATE TABLE tool_circle_requirement_version
(
    transaction_id     BIGINT NOT NULL REFERENCES transaction,
    end_transaction_id BIGINT REFERENCES transaction,
    operation_type     INT    NOT NULL,


    tool_id            BIGINT REFERENCES tool_description,
    circle_id          BIGINT REFERENCES circle
);
GRANT INSERT, UPDATE ON tool_circle_requirement_version TO "p2k16-web";
GRANT ALL ON tool_circle_requirement_version TO "p2k16-web";
