#!/usr/bin/env python

import sys
# ../../python is (once this test is being run) the source-dir python,
#    ../python is inside the build-directory
sys.path = [ '../../python/installroot', '../python/installroot' ] + sys.path

# Normal programming uses the package name, but in the build tree we don't
# from quick_der.rfc5280 import Certificate
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
