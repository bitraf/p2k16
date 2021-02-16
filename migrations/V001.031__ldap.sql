-- ----------------------------------------------------------------------
-- Tables and grants
-- ----------------------------------------------------------------------

DROP SCHEMA IF EXISTS "p2k16-ldap" CASCADE;
CREATE SCHEMA "p2k16-ldap";

SET SEARCH_PATH = "p2k16-ldap";

CREATE TABLE ldap_oc_mappings
(
    id            BIGINT      NOT NULL PRIMARY KEY,
    name          VARCHAR(64) NOT NULL,
    keytbl        VARCHAR(64) NOT NULL,
    keycol        VARCHAR(64) NOT NULL,
    create_proc   VARCHAR(255),
    delete_proc   VARCHAR(255),
    expect_return INT         NOT NULL
);

CREATE TABLE ldap_attr_mappings
(
    id            BIGINT       NOT NULL PRIMARY KEY,
    oc_map_id     INTEGER      NOT NULL REFERENCES ldap_oc_mappings (id),
    name          VARCHAR(255) NOT NULL,
    sel_expr      VARCHAR(255) NOT NULL,
    sel_expr_u    VARCHAR(255),
    from_tbls     VARCHAR(255) NOT NULL,
    join_where    VARCHAR(255),
    add_proc      VARCHAR(255),
    delete_proc   VARCHAR(255),
    param_order   INT          NOT NULL,
    expect_return INT          NOT NULL
);

CREATE TABLE ldap_entries_static
(
    id        BIGINT       NOT NULL PRIMARY KEY,
    dn        VARCHAR(255) NOT NULL,
    oc_map_id INTEGER      NOT NULL REFERENCES ldap_oc_mappings (id),
    parent    INT          NOT NULL,
    keyval    INT          NOT NULL,
    UNIQUE (oc_map_id, keyval),
    UNIQUE (dn)
);

CREATE TABLE ldap_entry_objclasses
(
    entry_id INTEGER NOT NULL REFERENCES ldap_entries_static (id),
    oc_name  VARCHAR(64)
);

-- ----------------------------------------------------------------------
-- Tables and mappings
-- ----------------------------------------------------------------------

-- Organizations, a thing that LDAP needs.

DROP TABLE IF EXISTS ldap_o;
CREATE TABLE ldap_o
(
    id   BIGINT PRIMARY KEY NOT NULL,
    name VARCHAR(100)       NOT NULL UNIQUE,
    dc   VARCHAR(100)       NOT NULL UNIQUE
);

INSERT INTO ldap_o(id, name, dc)
VALUES (1000, 'Bitraf', 'bitraf');

INSERT INTO ldap_oc_mappings(id, name, keytbl, keycol, create_proc, delete_proc, expect_return)
VALUES (200, 'organization', 'ldap_o', 'id', NULL, NULL, 0);

INSERT INTO ldap_attr_mappings(id, oc_map_id, name, sel_expr, from_tbls, join_where, add_proc, delete_proc,
                               param_order, expect_return)
VALUES (201, (select id from ldap_oc_mappings where name='organization'),
        'o',
        'ldap_o.name',
        'ldap_o',
        NULL,
        NULL,
        NULL, 3, 0),
       (202, (select id from ldap_oc_mappings where name='organization'),
        'dc',
        'dc',
        'ldap_o,ldap_entries AS dcObject,ldap_entry_objclasses AS auxObjectClass',
        'ldap_o.id=dcObject.keyval AND dcObject.oc_map_id=3 AND dcObject.id=auxObjectClass.entry_id AND auxObjectClass.oc_name=''dcObject''',
        NULL,
        NULL,
        3,
        0);


INSERT INTO ldap_entries_static(id, dn, oc_map_id, parent, keyval)
VALUES (10, 'dc=bitraf,dc=no', 200, 0, (SELECT id FROM ldap_o WHERE dc = 'bitraf'));

INSERT INTO ldap_entry_objclasses(entry_id, oc_name)
VALUES ((SELECT id FROM ldap_entries_static WHERE dn = 'dc=bitraf,dc=no'),
        'dcObject');

-- OUs, organization units. Basically containers for data of different kinds. Make ou=People and ou=Group,
-- Their DNs become ou=People,dc=bitraf,dc=no and ou=Group,dc=bitraf,dc=no.

DROP TABLE IF EXISTS ldap_ou;
CREATE TABLE ldap_ou
(
    id   BIGINT PRIMARY KEY NOT NULL,
    ou   VARCHAR(100)       NOT NULL UNIQUE
);

INSERT INTO ldap_ou(id, ou)
VALUES (2000, 'People'),
       (2001, 'Group');

INSERT INTO ldap_oc_mappings (id, name, keytbl, keycol, create_proc, delete_proc, expect_return)
VALUES (300, 'organizationalUnit', 'ldap_ou', 'id', NULL, NULL, 0);

INSERT INTO ldap_attr_mappings (id, oc_map_id, name, sel_expr, from_tbls, join_where, add_proc, delete_proc,
                                param_order, expect_return)
VALUES (302, (select id from ldap_oc_mappings where name='organizationalUnit'),
        'ou',
        'ou',
        'ldap_ou',
        NULL,
        NULL,
        NULL,
        3,
        0);

INSERT INTO ldap_entries_static(id, dn, oc_map_id, parent, keyval)
VALUES (11, 'ou=People,dc=bitraf,dc=no', 300, 0, (SELECT id FROM ldap_ou WHERE ou = 'People')),
       (12, 'ou=Group,dc=bitraf,dc=no', 300, 0, (SELECT id FROM ldap_ou WHERE ou = 'Group'));

INSERT INTO ldap_entry_objclasses(entry_id, oc_name)
VALUES ((SELECT id FROM ldap_entries_static WHERE dn = 'ou=People,dc=bitraf,dc=no'), 'organizationalUnit'),
       ((SELECT id FROM ldap_entries_static WHERE dn = 'ou=Group,dc=bitraf,dc=no'), 'organizationalUnit');

-- Map existing accounts

INSERT INTO ldap_oc_mappings(id, name, keytbl, keycol, create_proc, delete_proc, expect_return)
VALUES (100, 'inetOrgPerson', 'account', 'id', NULL, NULL, 0);

INSERT INTO ldap_attr_mappings(id, oc_map_id, name, sel_expr, from_tbls, join_where, add_proc, delete_proc,
                               param_order, expect_return)
VALUES (101, 100,
        'cn',
        'name',
        'account',
        NULL, NULL, NULL, 3, 0),
       (102, 100,
        'mail',
        'email',
        'account',
        NULL, NULL, NULL, 3, 0),
       (103, 100,
        'uid',
        'username',
        'account',
        NULL, NULL, NULL, 3, 0),
       (104, 100,
        'userPassword',
        '''{CRYPT}''||password',
        'account',
        NULL, NULL, NULL, 3, 0);


CREATE OR REPLACE VIEW ldap_entries AS
SELECT id, dn, oc_map_id, parent, keyval
FROM ldap_entries_static
UNION
SELECT id, 'uid=' || username || ',ou=People,dc=bitraf,dc=no', 100, 10, id
FROM public.account;

-- ----------------------------------------------------------------------
-- Grants
-- ----------------------------------------------------------------------

GRANT SELECT ON TABLE ldap_o TO "p2k16-ldap";
GRANT SELECT ON TABLE ldap_ou TO "p2k16-ldap";

GRANT SELECT ON ldap_entry_objclasses TO "p2k16-ldap";
GRANT SELECT ON ldap_entries TO "p2k16-ldap";
GRANT SELECT ON ldap_attr_mappings TO "p2k16-ldap";
GRANT SELECT ON ldap_oc_mappings TO "p2k16-ldap";

GRANT USAGE ON SCHEMA "p2k16-ldap" TO "p2k16-ldap";
GRANT SELECT ON public.account TO "p2k16-ldap";

SET search_path TO DEFAULT;
