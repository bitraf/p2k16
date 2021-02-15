BEGIN {
    keys[0] = "ODBC_PGDATABASE";
    keys[1] = "ODBC_PGHOST";
    keys[2] = "ODBC_PGPORT";

    keys[3] = "SLAPD_SUFFIX";
    keys[4] = "SLAPD_DBNAME";
    keys[5] = "SLAPD_DBUSER";
    keys[6] = "SLAPD_DBPASSWD";
}

{
    for (i in keys) {
        key = keys[i]
        if (ENVIRON[key] !~ /^$/ ) {
            gsub("%" key "%", ENVIRON[key])
        }
    }
    print($0)
}
