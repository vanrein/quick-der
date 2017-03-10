#DONE# share the bindata and ofslen structures with sub-objects (w/o cycles)
#DONE# add the packer data to the ASN1Object
#DONE# add a der_pack() method
#TODO# generate rfc1234.TypeName classes (or modules, or der_unpack functions)
#DONE# deliver ASN1Object from the der_unpack() called on rfc1234.TypeName
#DONE# manually program a module _quickder.so to adapt Quick DER to Python
#DONE# support returning None from OPTIONAL fields
#DONE# support a __delattr__ method (useful for OPTIONAL field editing)
#TODO# is there a reason, any reason, to maintain the (ofs,len) form in Python?


# We need two methods with Python wrapping in C plugin module _quickder:
# der_pack() and der_unpack() with proper memory handling
#  * Arrays of dercursor are passed as [(ofs,len)]
#  * Bindata is passed as Python strings
import _quickder


# The ASN1Object is a nested structure of class, accommodating nested fields.
# Nesting instances share the bindata and ofslen structures, which they modify
# to retain sharing.  The reason for this is that a future der_pack() on the
# class must use changes made in the nested objects as well as the main one.

class ASN1Object (object):

	def __init__ (self, der_packer='\x00', structure={}, ofslen=[], bindata=['']):
		ASN1Object.der_packer = der_packer
		ASN1Object.structure = structure
		ASN1Object.ofslen = ofslen
		ASN1Object.bindata = bindata
		for (k,v) in structure.items ():
			if type (k) != type (""):
				raise Exception ("ASN.1 structure keys can only be strings")
			if type (v) == type (13):
				ASN1Object.structure [k] = v
			elif type (v) == type ({}):
				ASN1Object.structure [k] = ASN1Object (
							bindata,
							structure [k],
							ofslen )
			else:
				raise Exception ("ASN.1 structure values can only be int or dict")

	def __setattr__ (self, name, val):
		if not ASN1Object.structure.has_key (name):
			raise AttributeError (name)
		val = str (val)
		siz = len (val)
		ofs = sum (map (len, ASN1Object.bindata))
		ASN1Object.ofslen [ASN1Object.structure [name]] = (ofs,siz)
		ASN1Object.bindata.append (val)

	def __delattr__ (self, name):
		if not ASN1Object.structure.has_key (name):
			raise AttributeError (name)
		idx = ASN1Object.structure [name]
		ASN1Object.ofslen [ASN1Object.structure [name]] = (None, None)

	def __getattr__ (self, name):
		if not ASN1Object.structure.has_key (name):
			raise AttributeError (name)
		idx = ASN1Object.structure [name]
		(ofs,siz) = ASN1Object.ofslen [ASN1Object.structure [name]]
		if ofs is None:
			# OPTIONAL or CHOICE element, not set to a value
			return None
		elm = 0
		while ofs >= len (ASN1Object.bindata [elm]):
			ofs = ofs - len (ASN1Object.bindata [elm])
			elm = elm + 1
		return ASN1Object.bindata [elm] [ofs:ofs+siz]

	def der_pack (self):
		"""Pack the current ASN1Object using DER notation.
		   Follow the syntax that was setup when this object
		   was created, usually after a der_unpack() operation
		   or a from_der (ClassName, bindata) or empty(ClassName)
		   call.  Return the bytes with the packed data.
		"""
		binvals = []
		for (ofs,siz) in self.ofslen:
			if ofs is None:
				binvals.append (None)
			else:
				elm = 0
				while ofs >= len (bindata [elm]):
					ofs = ofs - len (bindata [elm])
					elm = elm + 1
				binvals.append (bindata [elm] [ofs:ofs+siz])
		return _quickder.der_pack (self.der_packer, binvals)



# Usually, the GeneratedTypeNameClass is generated by asn2quickder in a module
# named by the specification, for instance, quick-der.rfc4511.LDAPMessage

class GeneratedTypeNameClass (ASN1Object):

	der_packer = '\x30\x04\x04\x00'
	structure = { 'hello': 0, 'world': 1 }
	ofslen = [ (0,5), (6,5) ]

	def __init__ (self, der_data=None):
		if der_data is not None:
			cursori = _quickder.der_unpack (der_packer, der_data, 2)
		else:
			der_data = ''
			cursori = [(None,None)] * 2 #TODO# 2 is an example
		print 'Setting der_data to', der_data
		print 'Setting cursori  to', cursori
		super (GeneratedTypeNameClass, self).__init__ (
			structure={ 'hello':0, 'world':1 }, 
			ofslen = cursori,
			bindata = [ der_data ] )


# A few package methods, instantiating a class

def der_unpack (der_data, cls):
	if der_data is None:
		raise Exception ('No DER data provided')
	return cls (der_data=der_data)

def empty(cls):
	return cls ()


# class LDAPMessage (ASN1Object):
if True:

	der_packer = '\x30\x04\x04\x00'
	structure = { 'hello': 0, 'world': 1 }
	ofslen = [ (0,5), (6,5) ]
	bindata = ['Hello World']

	# def unpack (self):
	# 	return ASN1Object (bindata=self.bindata, ofslen=self.ofslen, structure=self.structure)

	def unpack ():
		return ASN1Object (der_packer=der_packer, bindata=bindata, ofslen=ofslen, structure=structure)


# 
# class LDAPMessage2 (ASN1Object):
# 
# 	bindata = 'Hello World'
# 	ofslen = [ (0,5), (6,5) ]
# 	structure = { 'hello': 0, 'world': 1 }
# 
# 	def __init__ (self):
# 		super (LDAPMessage2,self).__init__ (
# 			bindata='Hello World',
# 			ofslen=[ (0,5), (6,5) ],
# 			structure={ 'hello':0, 'world':1 })
# 
# 
# # a1 = ASN1Wrapper (bindata, ofslen, structure)
# # a1 = ASN1Object (bindata, ofslen, structure)
# # a1 = LDAPMessage ()
# a1 = LDAPMessage2 ()

a1=unpack()

print 'Created a1'

print a1.hello, a1.world

a1.world = 'Wereld'
a1.hello = 'Motjo'

print a1.hello, a1.world

del a1.hello

print a1.hello, a1.world

a1.hello = 'Hoi'
print a1.hello, a1.world

pepe = a1.der_pack ()
print 'pepe.length =', len (pepe)
print 'pepe.data =', ''.join (map (lambda c:'%02x '%ord(c), pepe))

a3 = empty (GeneratedTypeNameClass)

print 'EMPTY:', a3.hello, a3.world

a2 = from_der (GeneratedTypeNameClass, pepe)

print 'PARSED:', a2.hello, a2.world

