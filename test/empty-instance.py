#!/usr/bin/env python

import sys
# ../../python is (once this test is being run) the source-dir python,
#    ../python is inside the build-directory
sys.path = [ '../../python/installroot', '../python/installroot' ] + sys.path

from quick_der.rfc4511 import LDAPMessage

lm = LDAPMessage ()

print lm
