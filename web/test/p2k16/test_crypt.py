import crypt


def test_crypt():
    password = "woot"
    encoded = "$6$Ytq2bVRLAA8MIiqR$g2IMx.oZ1TK2q6VPzK7b75z10VVxGTjc7v4sPTpkHvngc3NDmYoBQJO9PtSPLa9/EfYz2REV8FZTolNUJLK6u."
    recoded = crypt.crypt(password, encoded)
    assert encoded == recoded
