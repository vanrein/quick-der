#!/usr/bin/env python

from quick_der.rfc5280 import Certificate

der = open ('../test/verisign.der').read ()
crt = Certificate (derblob=der)

print 'WHOLE CERT:'
print crt
print

print 'TBSCERTIFICATE:'
print 'type is', type (crt.tbsCertificate)
print

exts = crt.tbsCertificate.extensions
print 'EXTENSIONS:', type (exts)
for exti in range (len (exts)):
	print '[' + str (exti) + '] ' + str (exts [exti].extnID) + ('CRITICAL ' if exts [exti].critical else '') + exts [exti].extnValue.encode ('hex')

print 'Succeeded'
