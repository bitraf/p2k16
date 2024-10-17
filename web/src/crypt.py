# SHAcrypt using SHA-512, after https://akkadia.org/drepper/SHA-crypt.txt.
#
# Copyright © 2024 Tony Garnock-Jones.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import hashlib
import secrets

alphabet = \
    [ord(c) for c in './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz']
permutation = [
    [0, 21, 42], [22, 43, 1], [44, 2, 23], [3, 24, 45],
    [25, 46, 4], [47, 5, 26], [6, 27, 48], [28, 49, 7],
    [50, 8, 29], [9, 30, 51], [31, 52, 10], [53, 11, 32],
    [12, 33, 54], [34, 55, 13], [56, 14, 35], [15, 36, 57],
    [37, 58, 16], [59, 17, 38], [18, 39, 60], [40, 61, 19],
    [62, 20, 41], [-1, -1, 63],
]
def encode(bs64):
    result = bytearray(4 * len(permutation))
    i = 0
    for group in permutation:
        g = lambda j: bs64[j] if j != -1 else 0
        bits = g(group[0]) << 16 | g(group[1]) << 8 | g(group[2])
        result[i] = alphabet[bits & 63]
        result[i+1] = alphabet[(bits >> 6) & 63]
        result[i+2] = alphabet[(bits >> 12) & 63]
        result[i+3] = alphabet[(bits >> 18) & 63]
        i = i + 4
    return bytes(result).decode('ascii')[:-2]

def repeats_of(n, bs): return bs * int(n / len(bs)) + bs[:n % len(bs)]
def digest(bs): return hashlib.sha512(bs).digest()

def crypt(password, salt = None, rounds = 5000):
    if salt is None: salt = encode(secrets.token_bytes(64))[:16].encode('ascii')
    salt = salt[:16]

    B = digest(password + salt + password)
    Ainput = password + salt + repeats_of(len(password), B)
    v = len(password)
    while v > 0:
        Ainput = Ainput + (B if v & 1 else password)
        v = v >> 1
    A = digest(Ainput)

    DP = digest(password * len(password))
    P = repeats_of(len(password), DP)
    DS = digest(salt * (16+A[0]))
    S = repeats_of(len(salt), DS)

    C = A
    for round in range(rounds):
        Cinput = b''
        Cinput = Cinput + (P if round & 1 else C)
        if round % 3: Cinput = Cinput + S
        if round % 7: Cinput = Cinput + P
        Cinput = Cinput + (C if round & 1 else P)
        C = digest(Cinput)

    if rounds == 5000:
        return '$6$' + salt.decode('ascii') + '$' + encode(C)
    else:
        return '$6$rounds=' + str(rounds) + '$' + salt.decode('ascii') + '$' + encode(C)

#---------------------------------------------------------------------------

def extract_salt_and_rounds(i): # i must be '$6$...'
    pieces = i.split('$')
    if pieces[1] != '6': raise TypeError('shacrypt512 only supports $6$ hashes')
    if pieces[2].startswith('rounds='):
        rounds = int(pieces[2][7:])
        if rounds < 1000: rounds = 1000
        if rounds > 999999999: rounds = 999999999
        return (pieces[3].encode('ascii'), rounds)
    else:
        return (pieces[2].encode('ascii'), 5000)

def password_ok(input_password, existing_crypted_password):
    (salt, rounds) = extract_salt_and_rounds(existing_crypted_password)
    return existing_crypted_password == shacrypt(input_password, salt, rounds)

if __name__ == '__main__':
    _test_password = 'Hello world!'.encode('ascii')
    _test_salt = 'saltstring'.encode('ascii')
    _test_rounds = 5000
    _test_crypted_password = '$6$saltstring$svn8UoSVapNtMuq1ukKS4tPQd8iKwSMHWjl/O817G3uBnIFNjnQJuesI68u4OTLiBFdcbYEdFCoEOfaS35inz1'
    assert shacrypt(_test_password, _test_salt, _test_rounds) == _test_crypted_password
    assert password_ok(_test_password, _test_crypted_password)

    _test_password = 'Hello world!'.encode('ascii')
    _test_salt = 'saltstringsaltstring'.encode('ascii')
    _test_rounds = 10000
    _test_crypted_password = '$6$rounds=10000$saltstringsaltst$OW1/O6BYHV6BcXZu8QVeXbDWra3Oeqh0sbHbbMCVNSnCM/UrjmM0Dp8vOuZeHBy/YTBmSK6H9qs/y3RnOaw5v.'
    assert shacrypt(_test_password, _test_salt, _test_rounds) == _test_crypted_password
    assert password_ok(_test_password, _test_crypted_password)

    import sys
    salt = None if len(sys.argv) < 2 else sys.argv[1].encode('ascii')
    print(shacrypt(sys.stdin.readline().strip().encode('utf-8'), salt))
