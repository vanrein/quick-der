#!/usr/bin/env python

import sys
# ../../python is (once this test is being run) the source-dir python,
#    ../python is inside the build-directory
sys.path = ['../../python/testing', '../python/testing'] + sys.path

from rfc4511 import LDAPMessage

lm = LDAPMessage()

print(lm)
