# Jenkins stores the passwords encrypted based on:
# http://stackoverflow.com/questions/4358146/what-password-encryption-hudson-is-using
#
# we can use the following piece of python code to generate the passwordHash
#
import hashlib
import sys

# USAGE: generate-password.py 'salt' 'password'

salt = sys.argv[1]
password = sys.argv[2]

inner_bit = "%s{%s}" % ( password, salt )
passwordHash = "%s:%s" % ( salt, hashlib.sha256(inner_bit.encode('utf8')).hexdigest())
print "password -> %s" % password
print "password hash -> %s" % passwordHash
