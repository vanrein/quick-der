#DONE# share the bindata and ofslen structures with sub-objects (w/o cycles)
#DONE# add the packer data to the ASN1Object
#DONE# add a der_pack() method
#DONE# deliver ASN1Object from the der_unpack() called on rfc1234.TypeName
#DONE# manually program a module _quickder.so to adapt Quick DER to Python
#DONE# support returning None from OPTIONAL fields
#DONE# support a __delattr__ method (useful for OPTIONAL field editing)
#DONE# is there a reason, any reason, to maintain the (ofs,len) form in Python?
#DONE# enjoy faster dict lookups with string interning (also done for fields)
#DONE# Created support for SEQUENCE OF and SET OF through post-processors
#DONE# SEQUENCE OF and SET OF for non-class-named objects cannot use ASN1Object
#DONE# split ASN1Object into abstract and ASN1ConstructedType (and more?)
#DONE# unpack INTEGER types to Python anysize integers (unpack_der_INTEGER?)
#DONE# (re)pack mapped Python types in der_pack(): int, set ([]), []
#TODO# generate rfc1234.TypeName classes (or modules, or der_unpack functions)


import string


if not 'intern' in dir (__builtins__):
	from sys import intern


# We need two methods with Python wrapping in C plugin module _quickder:
# der_pack() and der_unpack() with proper memory handling
#  * Arrays of dercursor are passed as [(ofs,len)]
#  * Bindata is passed as Python strings
import _quickder


# The ASN1Object is the abstract base class for ASN.1 objects.
# Data from subclasses is stored here, so subclasses can override the
# __getattr__() and __setattr__() methods, allowing obj.field notation.

class ASN1Object (object):

	"""The ASN1Object is an abstract base class for all the value holders
	   of ASN.1 data.  It has no value on its own.  Subclasses are the
	   following generic classes:
	     * `ASN1ConstructedType`
	     * `ASN1SequenceOf`
	     * `ASN1SetOf`
	     * `ASN1Atom`
	   The `asn2quickder` compiler creates further subclasses of these.
	   This means that all the data objects derived from unpacking DER
	   data are indirect subclasses of `ASN1Obejct`.
	"""

	pass


# The ASN1ConstructedType is a nested structure of class, accommodating nested fields.
# Nesting instances share the bindata list structures, which they modify
# to retain sharing.  The reason for this is that the _der_pack() on the
# class must use changes made in the nested objects as well as the main one.

#SHARED IN LOWEST CLASS: ._structure and ._der_packer
#STORED IN OBJECTS: ._fields, ._offset, ._bindata, ._numcursori

class ASN1ConstructedType (ASN1Object):

	"""The ASN.1 constructed types are `SEQUENCE`, `SET` and `CHOICE`.
	   Note that `SEQUENCE OF` and `SET OF` are not considered
	   constructed types.

	   Elements of constructed types can be addressed by their field name,
	   and the Python representation makes just that possible.  The result
	   of updates will automatically be incorporated into the binary data
	   that is used in upcoming _der_pack() invocations.

	   Construct subclasses of this class, with the following attributes:
	     * `_der_packer`
	     * `_structure` is a dictionary that maps field names to one of
	         - an integer index into `bindata[]`
	         - a subdictionary shaped like `_structure`
	         - singleton list capturing the element type of SEQUENCE OF
	         - singleton set  capturing the element type of SET OF
	         - `(class,...)` tuples referencing an `ASN1Object` subclass
	   These structures are also built by the `asn2quickder` compiler.
	"""

	def __init__ (self, bindata=[], ofs=0, structure=None):
		self._bindata = bindata
		self._offset = ofs
		self._fields = {}
		numcursori = 0
		# Static structure is generated from the ASN.1 grammar
		# Iterate over this structure to forming the instance data
		if structure is None:
			structure = self._structure
		for (k,v) in structure.items ():
			numcursori = numcursori + 1
			self._fields [k] = build_asn1 ( (k,v), bindata, ofs )
		self._numcursori = numcursori

	def _name2idx (self, name):
		while not self._fields.has_key (name):
			if name [-1:] == '_':
				name = name [:1]
				continue
			raise AttributeError (name)
		return self._fields [name]

	def __setattr__ (self, name, val):
		if name [0] != '_':
			idx = self._name2idx (name)
			self._bindata [idx] = val
		else:
			self.__dict__ [name] = val

	def __delattr__ (self, name):
		idx = self._name2idx (name)
		self._bindata [idx] = None

	def __getattr__ (self, name):
		idx = self._name2idx (name)
		return self._bindata [idx]

	def _der_pack (self):
		"""Pack the current ASN1ConstructedType using DER notation.
		   Follow the syntax that was setup when this object
		   was created, usually after a der_unpack() operation
		   or a der_unpack (ClassName, derblob) or empty(ClassName)
		   call.  Return the bytes with the packed data.
		"""
		bindata = []
		for bd in self._bindata [self._offset:self._offset+self._numcursori]:
			#TODO# list, set, ...
			bindata.append (bd)
		return _quickder.der_pack (self._der_packer, bindata)


class ASN1SequenceOf (ASN1Object,list):

	"""An ASN.1 representation for a SEQUENCE OF other ASN1Object values.

	   The instances of this class can be manipulated just like Python's
	   native list type.

	   TODO: Need to _der_pack() and get the result back into a context.
	"""

	def __init__ (self, cls, derblob):
		assert (issubclass (cls,ASN1Object))
		while len (derblob) > 0:
			(tag,ilen,hlen) = _quickder.der_header (derblob)
			if len (derblob) < hlen+ilen:
				raise Exception ('SEQUENCE OF elements must line up to a neat whole')
			print 'Creating class instance on', ''.join (map (lambda c:'%02x '%ord(c), derblob[:hlen+ilen]))
			self.append (cls (derblob [:hlen+ilen]))  #TODO# ofs?
			derblob = derblob [hlen+ilen:]

	def _der_pack (self):
		TODO


class ASN1SetOf (ASN1Object,set):

	"""An ASN.1 representation for a SET OF other ASN1Object values.

	   The instances of this class can be manipulated just like Python's
	   native set type.

	   TODO: Need to _der_pack() and get the result back into a context.
	"""

	def __init__ (self, cls, derblob):
		assert (issubclass (cls,ASN1Object))
		while len (derblob) > 0:
			(tag,ilen,hlen) = _quickder.der_header (derblob)
			if len (derblob) < hlen+ilen:
				raise Exception ('SET OF elements must line up to a neat whole')
			print 'Creating class instance on', ''.join (map (lambda c:'%02x '%ord(c), derblob[:hlen+ilen]))
			self.add (cls (derblob [:hlen+ilen]))  #TODO# ofs?
			derblob = derblob [hlen+ilen:]

	def _der_pack (self):
		TODO


class ASN1Atom (ASN1Object):

	"""An ASN.1 primitive object.  This is used for `INTEGER`, `REAL`,
	   `BOOLEAN`, `ENUMERATED` and the various `STRING`, `TIME` and
	    `OID` forms.

	   Note that `NULL` is not an ASN1Atom; it is represented in Python
	   as `None`.

	   The value contained is accessed through the value attribute, and
	   forms the literal byte representation without the DER header.

	   TODO: Map value changes to context for `_der_pack()` calls.
	"""

	value = ''
	offset = 0

	def __init__ (self, derblob='', ofs=0):
		self.value = derblob
		self.offset = ofs

	def get (self):
		return self.value

	def set (self, value):
		tv = type (value)
		if tv == str:
			self.value = value
		elif tv == int:
			strval = ''
			while value not in [0,-1]:
				byt = value & 0xff
				value = value >> 8
				strval = chr (byt) + strval
			if value == 0:
				if len (strval) > 0 and byt & 0x80 == 0x80:
					strval = chr (0x00) + strval
			else:
				if len (strval) == 0 or byt & 0x80 == 0x00:
					strval = chr (0xff) + strval
			self.value = strval
		else:
			raise ValueError ('ASN1Atom.set() only accepts int or str')

	__str__ = get

	def __int__ (self):
		if self.value == '':
			return 0
		retval = 0
		if ord (self.value [0]) & 0x80:
			retval = -1
		for byt in map (ord, self.value):
			retval = (retval << 8) + byt
		return retval


def build_asn1 ( (k,v), bindata, ofs):
	if type (k) != str:
		raise Exception ("ASN.1 structure keys can only be strings")
	# Interned strings yield faster dictionary lookups
	# Field names in Python are always interned
	k = intern (k.replace ('-', '_'))
	vt = type (v)
	if vt == int:
		# Numbers refer to a dercursor index number
		return ofs + v
	elif vt == tuple:
		# (class,suboffset) tuples are type references
		# such late linking allows any class order
		(subcls,subofs) = v
		assert (issubclass (subcls, ASN1Object))
		assert (type (subofs) == int)
		return subcls (bindata, ofs + subofs)
	elif vt == list:
		assert (len (v) == 1)
		return ASN1SequenceOf (v [0], bindata [ofs])
	elif vt == set:
		assert (len (v) == 1)
		return ASN1SetOf (v [0], bindata [ofs])
	elif vt == dict:
		# dictionaries are ASN.1 constructed types
		return ASN1ConstructedType (
					bindata,
					ofs,
					structure = structure [k] )
	else:
		raise ValueError ("ASN.1 structure must be int, dict, list, set or (subclass,suboffset)")


# Usually, the GeneratedTypeNameClass is generated by asn2quickder in a module
# named by the specification, for instance, quick-der.rfc4511.LDAPMessage

class GeneratedTypeNameClass (ASN1ConstructedType):

	_der_packer = '\x30\x04\x04\x00'
	_structure = { 'hello': 0, 'world': 1 }

	def __init__ (self, derblob=None, ofs=0):
		if derblob is not None:
			cursori = _quickder.der_unpack (self._der_packer, derblob, 2)
		else:
			cursori = [None] * 2 #TODO# 2 is an example
		super (GeneratedTypeNameClass, self).__init__ (
			bindata = cursori,
			ofs=ofs )


class OctetString (ASN1ConstructedType):

	_der_packer = '\x04\x00'
	_structure = { 'value':0 }

	def __init__ (self, derblob=None, ofs=0):
		if derblob is not None:
			print 'Using _der_packer =', ''.join (map (lambda c:'%02x '%ord(c), self._der_packer))
			print 'Using derblob =', ''.join (map (lambda c:'%02x '%ord(c), derblob))
			cursori = _quickder.der_unpack (self._der_packer, derblob, 1)
		else:
			cursori = [None] * 1 #TODO# 1 is an example
		super (OctetString, self).__init__ (
			bindata = cursori,
			ofs=ofs )


# A few package methods, instantiating a class

def empty(cls, ofs=0):
	if not issubclass (cls, ASN1Object):
		raise Exception ('You can only create an empty ASN1ConstructedType')
	return cls (ofs=ofs)


def der_pack_SEQUENCE_OF (self):
	retval = ''.join ( [ elem._der_pack () for elemn in self ] )
	return retval

der_pack_SET_OF = der_pack_SEQUENCE_OF


# This function can be used as "proc" entry when building an ASN1ConstructedType
def der_unpack_SEQUENCE_OF (cls, derblob, ofs=0, asn1type='SEQUENCE OF'):
	retval = []
	while len (derblob) > 0:
		(tag,ilen,hlen) = _quickder.der_header (derblob)
		print 'der_header (derblob) =', (tag,ilen,hlen)
		if len (derblob) < hlen+ilen:
			raise Exception (asn1type + ' elements must line up to a neat whole')
		print 'Creating class instance on', ''.join (map (lambda c:'%02x '%ord(c), derblob[:hlen+ilen]))
		retval.append (cls (derblob [:hlen+ilen], ofs))
		derblob = derblob [hlen+ilen:]
	#TODO:WHYNOT# retval._der_pack = der_pack_SEQUENCE_OF
	return retval


# This function can be used as "proc" entry when building an ASN1ConstructedType
def der_unpack_SET_OF (cls, derblob, ofs=0):
	retval = set (der_unpack_SEQUENCE_OF (
			cls, derblob, ofs=ofs, asn1type='SET OF'))
	#TODO:WHYNOT# retval._der_pack = der_pack_SET_OF
	return retval


def der_pack_INTEGER (ival):
	retval = ''
	while ival not in [0,-1]:
		byt = ival & 0xff
		ival = ival >> 8
		retval = chr (byt) + retval
	if ival == 0:
		if len (retval) > 0 and byt & 0x80 == 0x80:
			retval = chr (0x00) + retval
	else:
		if len (retval) == 0 or byt & 0x80 == 0x00:
			retval = chr (0xff) + retval
	return retval


# This function can be used as "proc" entry when interpreting INTEGER content
def der_unpack_INTEGER (cls_ignored, derblob, ofs_ignored=0):
	if derblob == '':
		return 0
	retval = 0
	if ord (derblob [0]) & 0x80:
		retval = -1
	for byt in map (ord, derblob):
		retval = (retval << 8) + byt
	return retval


def der_unpack (cls, derblob, ofs=0):
	if not issubclass (cls, ASN1Object):
		if cls == int:
			return der_unpack_INTEGER (derblob)
		elif cls == list:
			return der_unpack_SEQUENCE_OF (derblob)
		elif cls == set:
			return der_unpack_SET_OF (derblob)
		raise Exception ('You can only unpack to an ASN1ConstructedType')
	if derblob is None:
		raise Exception ('No DER data provided')
	return cls (derblob=derblob, ofs=ofs)


def der_pack (pyval):
	if isinstance (pyval, ASN1Object):
		return pyval._der_pack ()
	elif type (pyval) == int:
		return der_pack_INTEGER (pyval)
	elif type (pyval) == list:
		return der_pack_SEQUENCE_OF (pyval)
	elif type (pyval) == set:
		return der_pack_SET_OF (pyval)
	else:
		raise Exception ('Only ASN1ConstructedType instances, integers, lists and sets work for der_pack()')


# class LDAPMessage (ASN1ConstructedType):
if True:

	# _der_packer = '\x30\x04\x04\x00'
	# structure = { 'hello': 0, 'world': 1 }
	# bindata = ['Hello', 'World']
	derblob = '\x30\x0e\x04\x05\x48\x65\x6c\x6c\x6f\x04\x05\x57\x6f\x72\x6c\x64'

	# def unpack (self):
	# 	return ASN1ConstructedType (bindata=self.bindata)

	def unpack ():
		up = GeneratedTypeNameClass (derblob=derblob)
		# up.hello = 'Hello'
		# up.world = 'World'
		return up


# 
# class LDAPMessage2 (ASN1ConstructedType):
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
# # a1 = ASN1ConstructedType (bindata, ofslen, structure)
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

pepe = a1._der_pack ()
print 'pepe.length =', len (pepe)
print 'pepe.data =', ''.join (map (lambda c:'%02x '%ord(c), pepe))

(tag,ilen,hlen) = _quickder.der_header (pepe)
print 'der_header (pepe) =', (tag,ilen,hlen)
pepe2 = pepe [hlen:]
while len (pepe2) > 0:
	print 'pepe2.length =', len (pepe2)
	print 'pepe2.data =', ''.join (map (lambda c:'%02x '%ord(c), pepe2))
	(tag2,ilen2,hlen2) = _quickder.der_header (pepe2)
	print 'der_header (pepe2) =', (tag2,ilen2,hlen2)
	if len (pepe2) == hlen2+ilen2:
		print 'Will exactly reach the end of pepe2'
	pepe2 = pepe2 [hlen2+ilen2:]

pepe3 = der_unpack_SEQUENCE_OF (OctetString, pepe [hlen:], 0)
print 'pepe3 =', pepe3

pepe4 = der_unpack_SET_OF (OctetString, pepe [hlen:], 0)
print 'pepe4 =', pepe4

pepe5 = ASN1SequenceOf (OctetString, pepe [hlen:])
print 'pepe5 =', pepe5

pepe6 = ASN1SetOf (OctetString, pepe [hlen:])
print 'pepe6 =', pepe6

a3 = empty (GeneratedTypeNameClass)

print 'EMPTY:', a3.hello, a3.world

a2 = der_unpack (GeneratedTypeNameClass, pepe)

print 'PARSED:', a2.hello, a2.world

i1 = der_pack_INTEGER (12345)
print 'Packed 12345 into', ''.join (map (lambda c:'%02x '%ord(c), i1))
print 'Unpacking gives', der_unpack_INTEGER (None, i1)

i2 = der_pack_INTEGER (-12345)
print 'Packed -12345 into', ''.join (map (lambda c:'%02x '%ord(c), i2))
print 'Unpacking gives', der_unpack_INTEGER (None, i2)

i3 = ASN1Atom (i1)
print 'Atom with 12345 string is', ''.join (map (lambda c:'%02x '%ord(c), str (i3)))
print 'Atom int is', int (i3)

i4 = ASN1Atom (i2)
print 'Atom with -12345 string is', ''.join (map (lambda c:'%02x '%ord(c), str (i4)))
print 'Atom int is', int (i4)

i0 = ASN1Atom ()
print 'Atom without seting string is', ''.join (map (lambda c:'%02x '%ord(c), str (i0)))
print 'Atom int is', int (i0)
