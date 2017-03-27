#!/usr/bin/env python

import sys

sys.path = [ '../../python', '../python', 'quick-der', 'rfc/quick-der', '../rfc/quick-der' ] + sys.path

from rfc4511 import LDAPMessage

lm = LDAPMessage ()

print lm
