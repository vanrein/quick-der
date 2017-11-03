#!/usr/bin/env python

import sys
# ../../python is (once this test is being run) the source-dir python,
#    ../python is inside the build-directory
sys.path = [ '../../python/testing', '../python/testing' ] + sys.path

# Normal programming uses the package name, but in the build tree we don't
# from quick_der.rfc5280 import Certificate
from rfc5280 import Certificate
from quick_der.format import der_pack

der_in = open (sys.argv [1]).read ()
crt = Certificate (derblob=der_in)

print('WHOLE CERT:')
print(crt)
print()

der_out = der_pack (crt)
if der_out != der_in:
	print('DIFFERENT DER BLOBS IN AND OUT!!!')
	print('der_in  =', der_in [:30].encode ('hex'), '...')
	print('der_out =', der_out[:30].encode ('hex'), '...')
	of = open ('/tmp/verisign.out', 'w')
	of.write (der_out)
	of.close ()
	print('der_out written to /tmp/verisign.out -- perhaps compare with derdump')
	sys.exit (1)

print('TBSCERTIFICATE:')
print('type is' + type (crt.tbsCertificate))
print()

exts = crt.tbsCertificate.extensions
print('EXTENSIONS:')
print('type is ' + type (exts))
for exti in range (len (exts)):
	print('[' + str (exti) + '] ' + str (exts [exti].extnID if exts [exti] else '(no OID)') + ' ' + ('CRITICAL ' if exts [exti].critical else '') + str (exts [exti].extnValue if exts [exti].extnValue else '(no value)'))

print('Succeeded')
