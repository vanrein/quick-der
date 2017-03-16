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
#DONE# define names like DER_PACK_xxx and DER_TAG_xxx in quick_der.api
#DONE# need to distinguish DER NULL; represent not as None but a data object
#TODO# generate rfc1234.TypeName classes (or modules, or der_unpack functions)
#TODO# construct the __str__ value following ASN.1 value notation


import string
import time

#TODO# Apparently, intern() is not available inside packages?!?
if not 'intern' in dir (__builtins__):
	try:
		from sys import intern
	except ImportError:
		intern = lambda s: s

# We need three methods with Python wrapping in C plugin module _quickder:
# der_pack() and der_unpack() with proper memory handling, plus der_header()
#  * Arrays of dercursor are passed as arrays of (copied) Python strings
#  * Bindata is passed as Python strings
import _quickder


# Special markers for instructions for (un)packing syntax
DER_PACK_LEAVE = 0x00
DER_PACK_END = 0x00
DER_PACK_OPTIONAL = 0x3f
DER_PACK_CHOICE_BEGIN = 0x1f
DER_PACK_CHOICE_END = 0x1f
DER_PACK_ANY = 0xdf

# Flags to add to tags to indicate entering or storing them while (un)packing
DER_PACK_ENTER = 0x20
DER_PACK_STORE = 0x00
DER_PACK_MATCHBITS = (~ (DER_PACK_ENTER | DER_PACK_STORE) )

# Universal tags and macros for application, contextual, private tags
DER_TAG_BOOLEAN = 0x01
DER_TAG_INTEGER = 0x02
DER_TAG_BITSTRING = 0x03
DER_TAG_BIT_STRING = 0x03
DER_TAG_OCTETSTRING = 0x04
DER_TAG_OCTET_STRING = 0x04
DER_TAG_NULL = 0x05
DER_TAG_OBJECTIDENTIFIER = 0x06
DER_TAG_OBJECT_IDENTIFIER = 0x06
DER_TAG_OID = 0x06
DER_TAG_OBJECT_DESCRIPTOR = 0x07
DER_TAG_EXTERNAL = 0x08
DER_TAG_REAL = 0x09
DER_TAG_ENUMERATED = 0x0a
DER_TAG_EMBEDDEDPDV = 0x0b
DER_TAG_EMBEDDED_PDV = 0x0b
DER_TAG_UTF8STRING = 0x0c
DER_TAG_RELATIVEOID = 0x0d
DER_TAG_RELATIVE_OID = 0x0d
DER_TAG_SEQUENCE = 0x10
DER_TAG_SEQUENCEOF = 0x10
DER_TAG_SEQUENCE_OF = 0x10
DER_TAG_SET = 0x11
DER_TAG_SETOF = 0x11
DER_TAG_SET_OF = 0x11
DER_TAG_NUMERICSTRING = 0x12
DER_TAG_PRINTABLESTRING = 0x13
DER_TAG_T61STRING = 0x14
DER_TAG_TELETEXSTRING = 0x14
DER_TAG_VIDETEXSTRING = 0x15
DER_TAG_IA5STRING = 0x16
DER_TAG_UTCTIME = 0x17
DER_TAG_GENERALIZEDTIME = 0x18
DER_TAG_GRAPHICSTRING = 0x19
DER_TAG_VISIBLESTRING = 0x1a
DER_TAG_GENERALSTRING = 0x1b
DER_TAG_UNIVERSALSTRING = 0x1c
DER_TAG_CHARACTERSTRING = 0x1d
DER_TAG_CHARACTER_STRING = 0x1d
DER_TAG_BMPSTRING = 0x1e

DER_TAG_APPLICATION = lambda n: 0x40 | n
DER_TAG_CONTEXT = lambda n: 0x80 | n
DER_TAG_PRIVATE = lambda n: 0xc0 | n


#
# Mappings for primitive DER elements that map to native Python objects
#


def der_pack_STRING (sval):
	return sval


def der_unpack_STRING (derblob):
	return derblob


def der_pack_OID (oidstr):
	oidvals = map (int, oidstr.split ('.'))
	oidvals [1] = chr (oidvals [0] * 40 + oidvals [1])
	for oidx in range (len (oidvals)-1, 0, -1):
		enc = chr (oidval & 0x7f) + enc
		while oidval > 127:
			oidval >>= 7
			enc = chr (0x80 | (oidval & 0x7f)) + enc
	return enc


def der_unpack_OID (derblob):
	oidvals = [0]
	for byte in derblob:
		if byte & 0x80 != 0x00:
			oidvals [-1] = (oidvals [-1] << 7) | (byte & 0x7f)
		else:
			oidvals [-1] = (oidvals [-1] << 7) |  byte
			oidsvals.append (0)
	fst = oidvals [0] / 40
	snd = oidvals [1] % 40
	oidvals = [fst, snd] + oidvals [1:-1]
	retval = ''
	comma = ''
	for oidval in oidvals:
		retval = retval + '%d%s' % (oidval, comma)
		comma = ','
	# We intern the OID because it is commonly used as an index
	return intern (retval)


def der_pack_RELATIVE_OID (oidstr):
	raise NotImplementedError ('der_pack_RELATIVE_OID')


def der_unpack_RELATIVE_OID (oidstr):
	raise NotImplementedError ('der_unpack_RELATIVE_OID')


def der_pack_BITSTRING (bset):
	bits = '\x00'
	for bit in bitset:
		byte = 1 + (bit >> 3)
		if len (bits) < byte + 1:
			byte = byte + '\x00' * (byte + 1 - len (bits))
		bits [byte] = bits [byte] | (1 << (bit & 0x07))
	return bits


def der_unpack_BITSTRING (derblob):
	#TODO# Consider support of constructed BIT STRING types
	assert len (derblob) >= 1, 'Empty BIT STRING values cannot occur in DER'
	assert ord (derblob [0]) <= 7, 'BIT STRING values must have a first byte up to 7'
	bitnum = 8 * len (derblob) - 8 - ord (derblob [0])
	bitset = set ()
	for bit in range (bitnum):
		if derblob [(bit >> 3) + 1] & (1 << (bit & 0x07)) != 0:
			bitset.add (bit)
	return bitset


def der_pack_UTCTIME (tstamp):
	return time.strftime ('%g%m%d%H%M%SZ', tstamp)


def der_unpack_UTCTIME (derblob):
	return time.strptime ('%g%m%d%H%M%SZ', derblob)


def der_pack_GENERALIZEDTIME (tstamp):
	#TODO# No support for fractional seconds
	return time.strftime ('%G%m%d%H%M%SZ', tstamp)


def der_unpack_GENERALIZEDTIME (derblob):
	#TODO# No support for fractional seconds
	return time.strptime ('%G%m%d%H%M%SZ', derblob)


def der_pack_BOOLEAN (bval):
	return '\xff' if bval else '\x00'


def der_unpack_BOOLEAN (derblob):
	return derblob != '\x00' * len (derblob)


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


def der_unpack_INTEGER (derblob):
	if derblob == '':
		return 0
	retval = 0
	if ord (derblob [0]) & 0x80:
		retval = -1
	for byt in map (ord, derblob):
		retval = (retval << 8) + byt
	return retval


def der_pack_REAL (rval):
	raise NotImplementedError ('der_pack_REAL -- too many variations')
	# See X.690 section 8.5 -- base2, base10, ... yikes!
	if rval == 0.0:
		return ''
	else:
		pass

def der_unpack_REAL ():
	raise NotImplementedError ('der_pack_REAL -- too many variations')
	# See X.690 section 8.5 -- base2, base10, ... yikes!




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

	_der_packer = None
	_recipe     = None
	_numcursori = None

	def __init__ (self, derblob=None, bindata=None, offset=0, der_packer=None, recipe=None):
		"""Initialise the current object; abstract classes require
		   parameters with typing information (der_packer, recipe,
		   numcursori).  Instance data may be supplied through bindata
		   and a possible offset, with a fallback to derblob that
		   will use the subclasses' _der_unpack() methods to form the
		   _bindata values.  If neither bindata nor derblob are
		   supplied, then an empty instance is delivered.
		"""
		assert der_packer is not None or self._der_packer is not None, 'You or a class from asn2quickder must supply a DER_PACK_ sequence for use with Quick DER'
		assert recipe is not None or self._recipe is not None, 'You or a class from asn2quickder must supply a recipe for instantiating object structures'
		assert bindata is not None or derblob is not None or self._numcursori is not None, 'When no binary data is supplied, you or a class from asn2quickder must supply how many DER cursors are used'
		# Construct the type if so desired
		if der_packer:
			self._der_packer = der_packer
		if recipe:
			self._recipe     = recipe
		# Ensure presence of all typing data
		# Fill the instance data as supplied, or else make it empty
		if bindata:
			self._bindata    = bindata
			self._offset     = offset
			self.__init_bindata__ ()
		elif derblob:
			self._bindata    = _quickder.der_unpack (self._der_packer, derblob, self._numcursori)
			self._offset     = 0
			assert offset == 0, 'You supplied a derblob, so you cannot request any offset but 0'
			self.__init_bindata__ ()
		elif self._numcursori:
			self._bindata    = [ None ] * self._numcursori
			self._offset     = offset
			assert offset == 0, 'You supplied no initialisation data, so you cannot request any offset but 0'
			self.__init_bindata__ ()

	def __init_bindata__ (self):
		assert False, 'Expected __init_bindata__() method not found in ' + self.__class__.__name__


# The ASN1ConstructedType is a nested structure of named fields.
# Nesting instances share the bindata list structures, which they modify
# to retain sharing.  The reason for this is that the _der_pack() on the
# class must use changes made in the nested objects as well as the main one.

#SHARED IN LOWEST CLASS: ._recipe and ._der_packer
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
	     * `_recipe` is a dictionary that maps field names to one of
	         - an integer index into `bindata[]`
	         - a subdictionary shaped like `_recipe`
	         - singleton list capturing the element type of SEQUENCE OF
	         - singleton set  capturing the element type of SET OF
	         - `(class,offset)` tuples referencing an `ASN1Object` subclass
	   These recipes are also built by the `asn2quickder` compiler.
	"""

	def __init_bindata__ (self):
		"""The object has been setup with structural information in
		   _der_packer and _recipe, as well as instance data in
		   _bindata and _offset.  We now iterate over all the fields
		   in the _recipe to replace some or all entries in _bindata
		   with an ASN1Object subclass instance.
		   The last step of this procedure is to self-register into
		   _bindata [_offset], so as to support future _der_pack()
		   calls.
		"""
		assert type (self._recipe) == dict, 'ASN1ConstructedType instances must have a dictionary in their _recipe'
		self._fields = {}
		numcursori = 0
		# Static recipe is generated from the ASN.1 grammar
		# Iterate over this recipe to forming the instance data
		for (subfld,subrcp) in self._recipe.items ():
			if type (subfld) != str:
				raise Exception ("ASN.1 recipe keys can only be strings")
			# Interned strings yield faster dictionary lookups
			# Field names in Python are always interned
			subfld = intern (subfld.replace ('-', '_'))
			subval = build_asn1 (subrcp, self._bindata, self._offset)
			if isinstance (subval, ASN1Object):
				# The following moved into __init_bindata__():
				# self._bindata [self._offset] = subval
				# Native types may be assigned instead of subval
				numcursori = numcursori + subval._numcursori
			else:
				# Primitive: Index into _bindata; set in _fields
				self._fields [subfld] = subval
				numcursori = numcursori + 1
		self._numcursori = numcursori	# Though we don't need it...
		#HUH:WHY:DROP# self._bindata [self._offset] = self

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

	_der_packer = chr (DER_PACK_STORE | DER_TAG_SEQUENCE) + chr (DER_PACK_END)
	_numcursori = 1

	def __init_bindata__ (self):
		"""The object has been setup with structural information in
		   _der_packer and _recipe, as well as instance data in
		   _bindata [_offset].  We now split the instance data into
		   list elements that we each instantiate from the class in
		   the _recipe.
		   The last step of this procedure is to self-register into
		   _bindata [_offset], so as to support future _der_pack()
		   calls.
		"""
		assert self._recipe [0] == '_SEQOF', 'ASN1SequenceOf instances must have a _recipe tuple (\'_SEQOF\',...)'
		(_SEQOF,subpck,subrcp) = self._recipe
		derblob = self._bindata [self._offset]
		while len (derblob) > 0:
			(tag,ilen,hlen) = _quickder.der_header (derblob)
			if len (derblob) < hlen+ilen:
				raise Exception ('SEQUENCE OF elements must line up to a neat whole')
			subdta = derblob [:hlen+ilen]
			subcrs = _quickder.der_unpack (subpck,subdta,1)
			subval = build_asn1 (subrcp, subcrs, 0)
			self.append (subval)
			derblob = derblob [hlen+ilen:]
		self._bindata [self._offset] = self

	def _der_pack (self):
		return ''.join ( [ elem._der_pack () for elem in self ] )


class ASN1SetOf (ASN1Object,set):

	"""An ASN.1 representation for a SET OF other ASN1Object values.

	   The instances of this class can be manipulated just like Python's
	   native set type.

	   TODO: Need to _der_pack() and get the result back into a context.
	"""

	_der_packer = chr (DER_PACK_STORE | DER_TAG_SET) + chr (DER_PACK_END)
	_numcursori = 1

	def __init_bindata__ (self):
		"""The object has been setup with structural information in
		   _der_packer and _recipe, as well as instance data in
		   _bindata [_offset].  We now split the instance data into
		   set members that we each instantiate from the class in
		   the _recipe.
		   The last step of this procedure is to self-register into
		   _bindata [_offset], so as to support future _der_pack()
		   calls.
		"""
		assert self._recipe [0] == '_SETOF', 'ASN1SetOf instances must have a _recipe tuple (\'_SETOF\',...)'
		(_SETOF,subpck,subrcp) = self._recipe
		derblob = self._bindata [self._offset]
		while len (derblob) > 0:
			(tag,ilen,hlen) = _quickder.der_header (derblob)
			if len (derblob) < hlen+ilen:
				raise Exception ('SET OF elements must line up to a neat whole')
			subdta = derblob [:hlen+ilen]
			subcrs = _quickder.der_unpack (subpck,subdta,1)
			subval = build_asn1 (subrcp, subcrs, 0)
			self.add (subval)
			derblob = derblob [hlen+ilen:]
		self._bindata [self._offset] = self

	def _der_pack (self):
		"""Return the result of the `der_pack()` operation on this
		   element.
		"""
		return ''.join ( [ elem._der_pack () for elem in self ] )


class ASN1Atom (ASN1Object):

	"""An ASN.1 primitive object.  This is used for `INTEGER`, `REAL`,
	   `BOOLEAN`, `ENUMERATED` and the various `STRING`, `TIME` and
	    `OID` forms.

	   Note that `NULL` is also an ASN1Atom; it is **not** represented in
	   Python as `None` because that would make it difficult to detect a
	   construct like `NULL OPTIONAL` which may either be explicitly
	   `NULL` (and so have an `ASN1Atom` setup for it) or may be absent
	   in which case the generic handling through `None` applies to
	   indicate absense of an `OPTION` or `CHOICE` field.

	   The value contained is accessed through `get()` and `set(newval)`
	   methods, handling the literal byte representation contained in the
	   DER notation, right after its header.

	   TODO: Map value changes to context for `_der_pack()` calls.

	   TODO: Consider using the _der_packer, and/or having subclasses.
	"""

	_numcursori = 1

	# The following lists the data types that can be represented in an
	# ASN1Atom, but that might also find another format more suited to
	# their needs.  Each mapping finds a function that produces a more
	# suitable form.  This form is then better used instead of the
	# default # ASN1Atom representation, which is like a contained string
	# with get() and set() methods to see and change it.  The functions
	# mapped to interpret DER content and map it to a native type.
	_direct_data_map = {
		DER_TAG_BOOLEAN: der_unpack_BOOLEAN,
		DER_TAG_INTEGER: der_unpack_INTEGER,
		DER_TAG_BITSTRING: der_unpack_BITSTRING,
		DER_TAG_OCTETSTRING: der_unpack_STRING,
		#DEFAULT# DER_TAG_NULL: ASN1Atom,
		DER_TAG_OID: der_unpack_OID,
		#DEFAULT# DER_TAG_OBJECT_DESCRIPTOR: ASN1Atom,
		#DEFAULT# DER_TAG_EXTERNAL:  ASN1Atom,
		DER_TAG_REAL: der_unpack_REAL,
		DER_TAG_ENUMERATED: der_unpack_INTEGER,	#TODO# der2enum???
		#DEFAULT# DER_TAG_EMBEDDED_PDV: ASN1Atom,
		DER_TAG_UTF8STRING: der_unpack_STRING,
		DER_TAG_RELATIVE_OID: der_unpack_RELATIVE_OID,
		DER_TAG_NUMERICSTRING: der_unpack_STRING,
		DER_TAG_PRINTABLESTRING: der_unpack_STRING,
		DER_TAG_TELETEXSTRING: der_unpack_STRING,
		DER_TAG_VIDETEXSTRING: der_unpack_STRING,
		DER_TAG_IA5STRING: der_unpack_STRING,
		DER_TAG_UTCTIME: der_unpack_UTCTIME,
		DER_TAG_GENERALIZEDTIME: der_unpack_GENERALIZEDTIME,
		DER_TAG_GRAPHICSTRING: der_unpack_STRING,
		DER_TAG_VISIBLESTRING: der_unpack_STRING,
		DER_TAG_GENERALSTRING: der_unpack_STRING,
		DER_TAG_UNIVERSALSTRING: der_unpack_STRING,
		DER_TAG_CHARACTERSTRING: der_unpack_STRING,
		DER_TAG_BMPSTRING: der_unpack_STRING,
	}

	def __init_bindata__ (self):
		"""The object has been setup with structural information in
		   _der_packer and _recipe, as well as instance data in
		   _bindata [_offset].  We now proceed to parse the result
		   and, depending on its precise type, to decide on replacing
		   the _bindata [_offset] with this instance or, it decoding
		   to a native form in Python makes more sense, to setup such
		   a native form.  This actually means that these objects may
		   be dropped without actually being used; thanks to reference
		   counting the overhead should be tolerable, though it may
		   be avoided in a more clever approach.
		"""
		mytag = ord (self._der_packer [0]) & DER_PACK_MATCHBITS
		if mytag in self._direct_data_map:
			mapfun = self._direct_data_map [mytag]
			if self._bindata [self._offset] is None:
				myrepr = None
			else:
				myrepr = mapfun (self._bindata [self._offset])
		else:
			myrepr = self
		# Keep the binary string in _value; possibly change _bindata
		self._value = self._bindata [self._offset]
		self._bindata [self._offset] = myrepr

	def get (self):
		return self._value

	def set (self, derblob):
		if type (derblob) == str:
			self._value = derblob
		else:
			raise ValueError ('ASN1Atom.set() only accepts derblob strings')

	def __str__ (self):
		if self._value is not None:
			return self._value
		else:
			return ''

	def __len__ (self):
		return len (self._value)

	def _der_pack (self):
		"""Return the result of the `der_pack()` operation on this
		   element.
		"""
		#TODO# insert the header!
		return self._bindata [self._offset]


class ASN1Integer (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_INTEGER) + chr(DER_PACK_END)
	_recipe = 0

	def __int__ (self):
		return der_unpack_INTEGER (str (self))


def build_asn1 (recipe, bindata=[], ofs=0):
	"""Construct an ASN.1 structural element from a recipe and bindata.
	   with ofset.  The result can either be an ASN1Object subclass
	   instance or an offset into bindata.
	"""
	if type (recipe) == int:
		# Numbers refer to a dercursor index number
		offset = recipe
		return ofs + offset
	elif recipe [0] == '_NAMED':
		# dictionaries are ASN.1 constructed types
		(_NAMED,pck,map) = recipe
		return ASN1ConstructedType (
					recipe = map,
					der_packer = pck,
					bindata = bindata,
					offset = ofs )
	elif recipe [0] == '_SEQOF':
		(_SEQOF,subpck,subrcp) = recipe
		return ASN1SequenceOf (
					recipe = subrcp,
					der_packer = subpck,
					bindata = bindata,
					offset = ofs )
	elif recipe [0] == '_SETOF':
		(_SETOF,subpck,subrcp) = recipe
		return ASN1SetOf (
					recipe = subrcp,
					der_packer = subpck,
					bindata = bindata,
					offset = ofs )
	elif recipe [0] == '_TYPTR':
		# Reference to an ASN1Object subclass
		(_TYPTR,subcls,subofs) = recipe
		assert (issubclass (subcls, ASN1Object))
		assert (type (subofs) == int)
		return subcls (
					recipe = subcls._recipe,
					der_packer = subcls._der_packer,
					bindata = bindata,
					offset = ofs )
	else:
		# (class,suboffset) tuples are type names or user class names
		# Late linking of such names enables recursive dependencies
		(subcls,subofs) = recipe
		# subcls = eval (subcls)
		subcls = globals () [subcls]
		return subcls (
					recipe = subcls._recipe,
					der_packer = subcls._der_packer,
					bindata = bindata,
					offset = ofs + subofs )


# Usually, the GeneratedTypeNameClass is generated by asn2quickder in a module
# named by the specification, for instance, quick-der.rfc4511.LDAPMessage

class GeneratedTypeNameClass (ASN1ConstructedType):

	_der_packer = '\x30\x04\x04\x00\x00'
	_recipe = { 'hello': 0, 'world': 1 }
	_numcursori = 2


class OctetString (ASN1Atom):

	_der_packer = '\x04\x00'
	_recipe = 0


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
	return cls (derblob=derblob, offset=ofs)


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
	# recipe = { 'hello': 0, 'world': 1 }
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
# 	recipe = { 'hello': 0, 'world': 1 }
# 
# 	def __init__ (self):
# 		super (LDAPMessage2,self).__init__ (
# 			bindata='Hello World',
# 			ofslen=[ (0,5), (6,5) ],
# 			recipe={ 'hello':0, 'world':1 })
# 
# 
# # a1 = ASN1Wrapper (bindata, ofslen, recipe)
# # a1 = ASN1ConstructedType (bindata, ofslen, recipe)
# # a1 = LDAPMessage ()
# a1 = LDAPMessage2 ()

a1=GeneratedTypeNameClass (derblob='\x30\x0e\x04\x05\x48\x65\x6c\x6c\x6f\x04\x05\x57\x6f\x72\x6c\x64')

print 'Created a1:', a1

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

#TODO:FUNGONE# pepe3 = der_unpack_SEQUENCE_OF (OctetString, pepe [hlen:], 0)
#TODO:FUNGONE# print 'pepe3 =', pepe3

#TODO:FUNGONE# pepe4 = der_unpack_SET_OF (OctetString, pepe [hlen:], 0)
#TODO:FUNGONE# print 'pepe4 =', pepe4

pepe5 = ASN1SequenceOf (recipe=('_SEQOF',OctetString._der_packer,OctetString._recipe), derblob=pepe)
print 'pepe5 =', pepe5, '::', type (pepe5), '[0]::', type (pepe5 [0]), '[1]::', type (pepe5 [1])

pepe6 = ASN1SetOf (recipe=('_SETOF',OctetString._der_packer,OctetString._recipe), derblob=chr(0x31)+pepe[1:])
print 'pepe6 =', pepe6, '::', type (pepe6)

a3 = GeneratedTypeNameClass ()

print 'EMPTY:', a3
print 'FIELD:', a3.hello
print 'FIELD:', a3.world
print 'FIELD:', a3.hello, a3.world

a2 = der_unpack (GeneratedTypeNameClass, pepe)

print 'PARSED:', a2.hello, a2.world

i1 = der_pack_INTEGER (12345)
print 'Packed 12345 into', ''.join (map (lambda c:'%02x '%ord(c), i1))
print 'Unpacking gives', der_unpack_INTEGER (i1)

i2 = der_pack_INTEGER (-12345)
print 'Packed -12345 into', ''.join (map (lambda c:'%02x '%ord(c), i2))
print 'Unpacking gives', der_unpack_INTEGER (i2)

# i3 = ASN1Atom (bindata=[i1], der_packer=chr (DER_PACK_STORE | DER_TAG_INTEGER) + chr (DER_PACK_END), recipe=0 )
i3 = ASN1Integer (derblob=chr(2) + chr(len(i1)) + i1)
#CHANGED_TYPE# print 'Atom with 12345 string is', ''.join (map (lambda c:'%02x '%ord(c), str (i3))), 'length', len (i3)
print 'Atom int is', i3, '::', type (i3), 'with value', int (i3)

# i4 = ASN1Atom (bindata=[i2], der_packer=chr (DER_PACK_STORE | DER_TAG_INTEGER) + chr (DER_PACK_END), recipe=0 )
i4 = ASN1Integer (derblob=chr(2) + chr(len(i2)) + i2)
#CHANGED_TYPE# print 'Atom with -12345 string is', ''.join (map (lambda c:'%02x '%ord(c), str (i4))), 'length', len (i4)
print 'Atom int is', i4, '::', type (i4), 'with value', int (i4)

i0 = ASN1Integer ()
#CHANGED_TYPE# print 'Atom without seting string is', ''.join (map (lambda c:'%02x '%ord(c), str (i0))), 'length', len (i0)
print 'Atom int is', i0, '::', type (i0), 'with value', int (i0)

