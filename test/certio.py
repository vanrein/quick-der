#!/usr/bin/env python

import sys

sys.path = [ '../../python', '../python', 'quick-der', '../rfc/quick-der' ] + sys.path

from quick_der.rfc5280 import Certificate

der = open (sys.argv [1]).read ()
crt = Certificate (derblob=der)

print 'WHOLE CERT:'
print crt
print

print 'TBSCERTIFICATE:'
print 'type is', type (crt.tbsCertificate)
print

exts = crt.tbsCertificate.extensions
print 'EXTENSIONS:'
print 'type is', type (exts)
for exti in range (len (exts)):
	print '[' + str (exti) + '] ' + str (exts [exti].extnID if exts [exti] else '(no OID)') + ' ' + ('CRITICAL ' if exts [exti].critical else '') + str (exts [exti].extnValue if exts [exti].extnValue else '(no value)')

print 'Succeeded'
