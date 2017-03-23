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
#DONE# generate rfc1234.TypeName classes (or modules, or der_unpack functions)
#DONE# parse the ASN.1 value notations used in RFCs: only INTEGER and OID
#DONE# resolve recursion by introducing typerefs (and lazy link + substitute)
#DONE# gen & ref _context variable in each generated class, set to _globals()
#TODO# construct the __str__ value following ASN.1 value notation


import string
import time

if not 'intern' in dir (globals () ['__builtins__']):
	try:
		from sys import intern
	except:
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
DER_TAG_VIDEOTEXSTRING = 0x15
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


def der_pack_OID (oidstr, hdr=False):
	oidvals = map (int, oidstr.split ('.'))
	oidvals [1] += 40 * oidvals [0]
	enc = ''
	for oidx in range (len (oidvals)-1, 0, -1):
		oidval = oidvals [oidx]
		enc = chr (oidval & 0x7f) + enc
		while oidval > 127:
			oidval >>= 7
			enc = chr (0x80 | (oidval & 0x7f)) + enc
	if hdr:
		enc = _quickder.der_pack ('\x06\x00', [enc])
	return enc


def der_unpack_OID (derblob):
	oidvals = [0]
	for byte in map (ord, derblob):
		if byte & 0x80 != 0x00:
			oidvals [-1] = (oidvals [-1] << 7) | (byte & 0x7f)
		else:
			oidvals [-1] = (oidvals [-1] << 7) |  byte
			oidvals.append (0)
	fst = oidvals [0] / 40
	snd = oidvals [0] % 40
	oidvals = [fst, snd] + oidvals [1:-1]
	retval = '.'.join (map (str, oidvals))
	return intern (retval)


def der_pack_RELATIVE_OID (oidstr):
	raise NotImplementedError ('der_pack_RELATIVE_OID')


def der_unpack_RELATIVE_OID (oidstr):
	raise NotImplementedError ('der_unpack_RELATIVE_OID')


def der_pack_BITSTRING (bitset):
	bits = [0]
	for bit in bitset:
		byte = 1 + (bit >> 3)
		if len (bits) < byte + 1:
			bits = bits + [0] * (byte + 1 - len (bits))
		bits [byte] |= (1 << (bit & 0x07))
	return ''.join (map (chr,bits))


def der_unpack_BITSTRING (derblob):
	#TODO# Consider support of constructed BIT STRING types
	assert len (derblob) >= 1, 'Empty BIT STRING values cannot occur in DER'
	assert ord (derblob [0]) <= 7, 'BIT STRING values must have a first byte up to 7'
	bitnum = 8 * len (derblob) - 8 - ord (derblob [0])
	bitset = set ()
	for bit in range (bitnum):
		if ord (derblob [(bit >> 3) + 1]) & (1 << (bit & 0x07)) != 0:
			bitset.add (bit)
	return bitset


def der_pack_UTCTIME (tstamp):
	return time.strftime (pstamp, '%y%m%d%H%M%SZ')


def der_unpack_UTCTIME (derblob):
	return time.strptime (derblob, '%y%m%d%H%M%SZ')


def der_pack_GENERALIZEDTIME (tstamp):
	#TODO# No support for fractional seconds
	return time.strftime (tstamp, '%Y%m%d%H%M%SZ')


def der_unpack_GENERALIZEDTIME (derblob):
	#TODO# No support for fractional seconds
	return time.strptime (derblob, '%Y%m%d%H%M%SZ')


def der_pack_BOOLEAN (bval):
	return '\xff' if bval else '\x00'


def der_unpack_BOOLEAN (derblob):
	return derblob != '\x00' * len (derblob)


def der_pack_INTEGER (ival, hdr=False):
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
	if hdr:
		retval = _quickder.der_pack ('\x02\x00', [retval])
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

	def __init__ (self, derblob=None, bindata=None, offset=0, der_packer=None, recipe=None, context=None):
		"""Initialise the current object; abstract classes require
		   parameters with typing information (der_packer, recipe,
		   numcursori).  Instance data may be supplied through bindata
		   and a possible offset, with a fallback to derblob that
		   will use the subclasses' _der_unpack() methods to form the
		   _bindata values.  If neither bindata nor derblob are
		   supplied, then an empty instance is delivered.  The optional
		   context defines the globals() map in which type references
		   should be resolved.
		"""
		#TODO:OLD# assert der_packer is not None or self._der_packer is not None, 'You or a class from asn2quickder must supply a DER_PACK_ sequence for use with Quick DER'
		assert (bindata is not None and recipe is not None) or der_packer is not None or self._der_packer is not None, 'You or a class from asn2quickder must supply a DER_PACK_ sequence for use with Quick DER'
		assert recipe is not None or self._recipe is not None, 'You or a class from asn2quickder must supply a recipe for instantiating object structures'
		#TODO:OLD# assert bindata is not None or derblob is not None or self._numcursori is not None, 'When no binary data is supplied, you or a class from asn2quickder must supply how many DER cursors are used'
		#TODO:NEW:MAYBENOTNEEDED# assert self._numcursori is not None, 'You should always indicate how many values will be stored'
		assert context is not None or getattr(self, "_context", None) is not None, 'You or a subclass definition should provide a context for symbol resolution'
		# Construct the type if so desired
		if der_packer:
			self._der_packer = der_packer
		if recipe:
			self._recipe     = recipe
		if context:
			self._context    = context
		# Ensure presence of all typing data
		# Fill the instance data as supplied, or else make it empty
		if bindata:
			self._bindata    = bindata
			self._offset     = offset
			self.__init_bindata__ ()
		elif derblob:
			self._bindata    = _quickder.der_unpack (self._der_packer, derblob, self._numcursori)
			assert len (self._bindata) == self._numcursori, 'Wrong number of values returned from der_unpack()'
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
		assert self._recipe [0] == '_NAMED', 'ASN1ConstructedType instances must have a dictionary in their _recipe'
		(_NAMED,recp) = self._recipe
		self._fields = {}
		# Static recipe is generated from the ASN.1 grammar
		# Iterate over this recipe to form the instance data
		for (subfld,subrcp) in recp.items ():
			if type (subfld) != str:
				raise Exception ("ASN.1 recipe keys can only be strings")
			# Interned strings yield faster dictionary lookups
			# Field names in Python are always interned
			subfld = intern (subfld.replace ('-', '_'))
			self._fields [subfld] = self._offset  # fallback
			subval = build_asn1 (self._context, subrcp, self._bindata, self._offset)
			if type (subval) == int:
				# Primitive: Index into _bindata; set in _fields
				self._fields [subfld] += subval
			elif subval.__class__ == ASN1Atom:
				# The following moved into __init_bindata__():
				# self._bindata [self._offset] = subval
				# Native types may be assigned instead of subval
				pass
				print 'Not placing field', subfld, 'subvalue ::', type (subval)
			elif isinstance (subval, ASN1Object):
				self._fields [subfld] = subval
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
		if type (idx) == int:
			return self._bindata [idx]
		else:
			return idx

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

	def __str__ (self):
		retval = '{\n    '
		comma = ''
		for (name,value) in self._fields.items ():
			if type (value) == int:
				value = self._bindata [value]
			if value is None:
				continue
			if isinstance (value, ASN1Atom) and value.get () is None:
				continue
			newval = str (value).replace ('\n', '\n    ')
			retval = retval + comma + name + ' ' + newval
			comma = ',\n    '
		retval = retval + ' }'
		return retval


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
		(_SEQOF,allidx,subpck,subnum,subrcp) = self._recipe
		#TODO:DEBUG# print 'SEQUENCE OF from', self._offset, 'to', allidx, 'element recipe =', subrcp
		#TODO:DEBUG# print 'len(_bindata) =', len (self._bindata), '_offset =', self._offset, 'allidx =', allidx
		derblob = self._bindata [self._offset]
		while len (derblob) > 0:
			#TODO:DEBUG# print 'Getting the header from ' + ' '.join (map (lambda x: x.encode ('hex'), derblob [:5])) + '...'
			(tag,ilen,hlen) = _quickder.der_header (derblob)
			if len (derblob) < hlen+ilen:
				raise Exception ('SEQUENCE OF elements must line up to a neat whole')
			subdta = derblob [:hlen+ilen]
			subcrs = _quickder.der_unpack (subpck,subdta,subnum)
			#TODO:ALLIDX# subval = build_asn1 (self._context, subrcp, subcrs, allidx)
			subval = build_asn1 (self._context, subrcp, subcrs, 0)
			self.append (subval)
			derblob = derblob [hlen+ilen:]
		#TODO:GENERIC# self._bindata [self._offset] = self

	def _der_pack (self):
		return ''.join ( [ elem._der_pack () for elem in self ] )

	def __str__ (self):
		entries = ',\n'.join ([str(x) for x in self])
		entries.replace ('\n', '\n    ')
		return 'SEQUENCE { ' + entries + ' }'


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
		(_SETOF,allidx,subpck,subnum,subrcp) = self._recipe
		#TODO:DEBUG# print 'SET OF from', self._offset, 'to', allidx, 'element recipe =', subrcp
		#TODO:DEBUG# print 'len(_bindata) =', len (self._bindata), '_offset =', self._offset, 'allidx =', allidx
		derblob = self._bindata [self._offset]
		while len (derblob) > 0:
			(tag,ilen,hlen) = _quickder.der_header (derblob)
			if len (derblob) < hlen+ilen:
				raise Exception ('SET OF elements must line up to a neat whole')
			subdta = derblob [:hlen+ilen]
			subcrs = _quickder.der_unpack (subpck,subdta,subnum)
			#TODO:ALLIDX# subval = build_asn1 (self._context, subrcp, subcrs, allidx)
			subval = build_asn1 (self._context, subrcp, subcrs, 0)
			self.add (subval)
			derblob = derblob [hlen+ilen:]
		#TODO:GENERIC# self._bindata [self._offset] = self

	def _der_pack (self):
		"""Return the result of the `der_pack()` operation on this
		   element.
		"""
		return ''.join ( [ elem._der_pack () for elem in self ] )

	def __str__ (self):
		entries = ',\n'.join ([str(x) for x in self])
		entries.replace ('\n', '\n    ')
		return 'SET { ' + entries + ' }'


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
	_recipe = 0
	_context = {}

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
		DER_TAG_VIDEOTEXSTRING: der_unpack_STRING,
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

	#OLD# 	def __str__ (self):
	#OLD# 		if self._value is not None:
	#OLD# 			return self._value
	#OLD# 		else:
	#OLD# 			return ''

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = "'" + self.get ().encode ('hex') + "'H"
		else:
			retval = 'None'
		return retval

	def __len__ (self):
		if self._value:
			return len (self._value)
		else:
			return 0

	def _der_pack (self):
		"""Return the result of the `der_pack()` operation on this
		   element.
		"""
		#TODO# insert the header!
		return self._bindata [self._offset]


class ASN1Boolean (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_BOOLEAN) + chr(DER_PACK_END)

	def __str__ (self):
		if self.get ():
			return 'TRUE'
		else:
			return 'FALSE'


class ASN1Integer (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_INTEGER) + chr(DER_PACK_END)

	def __int__ (self):
		return der_unpack_INTEGER (self.get ())

	def __str__ (self):
		return str (self.__int__ ())


class ASN1BitString (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_BITSTRING) + chr(DER_PACK_END)

	def test (self, bit):
		return bit in self._bindata [self._offset]

	def set (self, bit):
		self._bindata [self._offset].add (bit)

	def clear (self, bit):
		self._bindata [self._offset].remove (bit)


class ASN1OctetString (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_OCTETSTRING) + chr(DER_PACK_END)


class ASN1Null (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_NULL) + chr(DER_PACK_END)

	def __str__ (self):
		return 'NULL'


class ASN1OID (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_OID) + chr(DER_PACK_END)

	def __str__ (self):
		oidstr = der_unpack_OID (self.get ())
		return '{ ' + oidstr.replace ('.', ' ') + ' }'


class ASN1Real (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_REAL) + chr(DER_PACK_END)


class ASN1Enumerated (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_ENUMERATED) + chr(DER_PACK_END)


class ASN1UTF8String (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_UTF8STRING) + chr(DER_PACK_END)

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1RelativeOID (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_RELATIVE_OID) + chr(DER_PACK_END)


class ASN1NumericString (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_NUMERICSTRING) + chr(DER_PACK_END)

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1PrintableString (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_PRINTABLESTRING) + chr(DER_PACK_END)

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1TeletexString (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_TELETEXSTRING) + chr(DER_PACK_END)

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1VideotexString (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_VIDEOTEXSTRING) + chr(DER_PACK_END)

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1IA5String (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_IA5STRING) + chr(DER_PACK_END)

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1UTCTime (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_UTCTIME) + chr(DER_PACK_END)

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1GeneralizedTime (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_GENERALIZEDTIME) + chr(DER_PACK_END)

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1GraphicString (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_GRAPHICSTRING) + chr(DER_PACK_END)


class ASN1VisibleString (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_VISIBLESTRING) + chr(DER_PACK_END)

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1GeneralString (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_GENERALSTRING) + chr(DER_PACK_END)

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1UniversalString (ASN1Atom):

	_der_packer = chr(DER_PACK_STORE | DER_TAG_UNIVERSALSTRING) + chr(DER_PACK_END)

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1Any (ASN1Atom):

	def __init_bindata__ (self):
		"""The object has been setup with structural information in
		   _der_packer and _recipe, as well as instance data in
		   _bindata [_offset].  Since this is the ANY object, any
		   parsing of its value is deferred until after set_class()
		   has been invoked.

		   Note that ANY is treated in a slightly different manner
		   from "normal" data; it is stored with the inclusion of
		   headers, simply because there was nothing to match them
		   against -- so all validating parsing remains to be done.
		"""
		self._value = self._bindata [self._offset]

	_der_packer = chr(DER_PACK_ANY) + chr(DER_PACK_END)
	_class = None

	def set (self, val):
		"""You cannot set the value of an ANY type object.  You may
		   however get() it and then you may try to use set() on the
		   result.  In other words, ANY will always remain an
		   intermediate step in the data path.
		"""
		assert False, 'You cannot set the value of an ANY type object'

	def set_class (self, cls):
		"""Set the class of an ANY type object.  This can be done at
		   most once.  The operation involves parsing the data with
		   the provided class and forming an instance from it, which
		   is made available through the get() method.  Note that the
		   class must be a subclass of ASN1Object.
		"""
		assert issubclass (cls, ASN1Object), 'ANY must be made concrete with a subtype of ASN1Object'
		assert self._class == None, 'ANY type has already been made concrete'
		self._class = cls
		self._value = cls (
					recipe = cls._recipe,
					der_packer = cls._der_packer,
					derblob = self._bindata [self._offset],
					offset = 0,
					context = cls._context )


def build_asn1 (context, recipe, bindata=[], ofs=0, outer_class=None):
	"""Construct an ASN.1 structural element from a recipe and bindata.
	   with ofset.  The result can either be an ASN1Object subclass
	   instance or an offset into bindata.  The context is used to lookup
	   identifiers during lazy binding, normally it is set to self._context
	   for a generated class, and it would reference the globals() context
	   of that class definition.
	"""
	if type (recipe) == int:
		# Numbers refer to a dercursor index number
		offset = recipe
		return ofs + offset
	elif recipe [0] == '_NAMED':
		# dictionaries are ASN.1 constructed types
		#TODO:OLD# (_NAMED,pck,map) = recipe
		(_NAMED,map) = recipe
		return ASN1ConstructedType (
					recipe = recipe,
					#TODO:OLD# der_packer = pck,
					bindata = bindata,
					offset = ofs,
					context = context )
	elif recipe [0] in ['_SEQOF', '_SETOF']:
		(_STHOF,allidx,subpck,subnum,subrcp) = recipe
		if outer_class:
			cls = outer_class
		elif _STHOF == '_SEQOF':
			cls = ASN1SequenceOf
		else:
			cls = ASN1SetOf
		packer = subpck [0]
		if packer is None:
			# Lazy linking:
			packer = ''
			for idx in range (1, len (subpck)):
				if subpck [idx] [:1] == '?':
					new = context [subpck [idx] [1:]]
				else:
					new = 0x00
					for elm in subpck [idx].split ('|'):
						elm = elm.strip ()
						new = new | globals () [elm]
					new = chr (new)
				packer += new
			packer += chr (DER_PACK_END)
			# Memorise linking result:
			subpck [0] = packer
			del subpck [1:]
		return cls (
					recipe = recipe,
					der_packer = subpck [0],
					bindata = bindata,
					offset = allidx,
					context = context )
	elif recipe [0] == '_TYPTR':
		# Reference to an ASN1Object subclass
		(_TYPTR,[subcls],subofs) = recipe
		if type (subcls) == str:
			if subcls [:5] == '_api.':
				context = context ['_api'].__dict__
				subcls = subcls [5:]
			elif subcls [:4] == 'ASN1':
				context = context ['_api'].__dict__
			subcls = context [subcls]	# lazy link
			recipe [1] [0] = subcls		# memorise
		assert issubclass (subcls, ASN1Object), 'Recipe ' + repr (recipe) + ' does not subclass ASN1Object'
		assert type (subofs) == int, 'Recipe ' + repr (recipe) + ' does not have an integer sub-offset'
		return subcls (
					recipe = subcls._recipe,
					der_packer = subcls._der_packer,
					bindata = bindata,
					offset = ofs + subofs,
					context = context )
	else:
		assert False, 'Unknown recipe tag ' + str (recipe [0])


# Usually, the GeneratedTypeNameClass is generated by asn2quickder in a module
# named by the specification, for instance, quick-der.rfc4511.LDAPMessage

class GeneratedTypeNameClass (ASN1ConstructedType):

	_der_packer = '\x30\x04\x04\x00\x00'
	_recipe = { 'hello': 0, 'world': 1 }
	_numcursori = 2



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

#TESTCODE:TODO:OLD# a1=GeneratedTypeNameClass (derblob='\x30\x0e\x04\x05\x48\x65\x6c\x6c\x6f\x04\x05\x57\x6f\x72\x6c\x64')
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# print 'Created a1:', a1
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# print a1.hello, a1.world
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# a1.world = 'Wereld'
#TESTCODE:TODO:OLD# a1.hello = 'Motjo'
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# print a1.hello, a1.world
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# del a1.hello
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# print a1.hello, a1.world
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# a1.hello = 'Hoi'
#TESTCODE:TODO:OLD# print a1.hello, a1.world
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# pepe = a1._der_pack ()
#TESTCODE:TODO:OLD# print 'pepe.length =', len (pepe)
#TESTCODE:TODO:OLD# print 'pepe.data =', ''.join (map (lambda c:'%02x '%ord(c), pepe))
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# (tag,ilen,hlen) = _quickder.der_header (pepe)
#TESTCODE:TODO:OLD# print 'der_header (pepe) =', (tag,ilen,hlen)
#TESTCODE:TODO:OLD# pepe2 = pepe [hlen:]
#TESTCODE:TODO:OLD# while len (pepe2) > 0:
#TESTCODE:TODO:OLD# 	print 'pepe2.length =', len (pepe2)
#TESTCODE:TODO:OLD# 	print 'pepe2.data =', ''.join (map (lambda c:'%02x '%ord(c), pepe2))
#TESTCODE:TODO:OLD# 	(tag2,ilen2,hlen2) = _quickder.der_header (pepe2)
#TESTCODE:TODO:OLD# 	print 'der_header (pepe2) =', (tag2,ilen2,hlen2)
#TESTCODE:TODO:OLD# 	if len (pepe2) == hlen2+ilen2:
#TESTCODE:TODO:OLD# 		print 'Will exactly reach the end of pepe2'
#TESTCODE:TODO:OLD# 	pepe2 = pepe2 [hlen2+ilen2:]
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# #TODO:FUNGONE# pepe3 = der_unpack_SEQUENCE_OF (ASN1OctetString, pepe [hlen:], 0)
#TESTCODE:TODO:OLD# #TODO:FUNGONE# print 'pepe3 =', pepe3
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# #TODO:FUNGONE# pepe4 = der_unpack_SET_OF (ASN1OctetString, pepe [hlen:], 0)
#TESTCODE:TODO:OLD# #TODO:FUNGONE# print 'pepe4 =', pepe4
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# pepe5 = ASN1SequenceOf (recipe=('_SEQOF',ASN1OctetString._der_packer,ASN1OctetString._recipe), derblob=pepe)
#TESTCODE:TODO:OLD# print 'pepe5 =', pepe5, '::', type (pepe5), '[0]::', type (pepe5 [0]), '[1]::', type (pepe5 [1])
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# pepe6 = ASN1SetOf (recipe=('_SETOF',ASN1OctetString._der_packer,ASN1OctetString._recipe), derblob=chr(0x31)+pepe[1:])
#TESTCODE:TODO:OLD# print 'pepe6 =', pepe6, '::', type (pepe6)
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# a3 = GeneratedTypeNameClass ()
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# print 'EMPTY:', a3
#TESTCODE:TODO:OLD# print 'FIELD:', a3.hello
#TESTCODE:TODO:OLD# print 'FIELD:', a3.world
#TESTCODE:TODO:OLD# print 'FIELD:', a3.hello, a3.world
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# a2 = der_unpack (GeneratedTypeNameClass, pepe)
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# print 'PARSED:', a2.hello, a2.world
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# i1 = der_pack_INTEGER (12345)
#TESTCODE:TODO:OLD# print 'Packed 12345 into', ''.join (map (lambda c:'%02x '%ord(c), i1))
#TESTCODE:TODO:OLD# print 'Unpacking gives', der_unpack_INTEGER (i1)
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# i2 = der_pack_INTEGER (-12345)
#TESTCODE:TODO:OLD# print 'Packed -12345 into', ''.join (map (lambda c:'%02x '%ord(c), i2))
#TESTCODE:TODO:OLD# print 'Unpacking gives', der_unpack_INTEGER (i2)
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# # i3 = ASN1Atom (bindata=[i1], der_packer=chr (DER_PACK_STORE | DER_TAG_INTEGER) + chr (DER_PACK_END), recipe=0 )
#TESTCODE:TODO:OLD# i3 = ASN1Integer (derblob=chr(2) + chr(len(i1)) + i1)
#TESTCODE:TODO:OLD# #CHANGED_TYPE# print 'Atom with 12345 string is', ''.join (map (lambda c:'%02x '%ord(c), str (i3))), 'length', len (i3)
#TESTCODE:TODO:OLD# print 'Atom int is', i3, '::', type (i3), 'with value', int (i3)
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# # i4 = ASN1Atom (bindata=[i2], der_packer=chr (DER_PACK_STORE | DER_TAG_INTEGER) + chr (DER_PACK_END), recipe=0 )
#TESTCODE:TODO:OLD# i4 = ASN1Integer (derblob=chr(2) + chr(len(i2)) + i2)
#TESTCODE:TODO:OLD# #CHANGED_TYPE# print 'Atom with -12345 string is', ''.join (map (lambda c:'%02x '%ord(c), str (i4))), 'length', len (i4)
#TESTCODE:TODO:OLD# print 'Atom int is', i4, '::', type (i4), 'with value', int (i4)
#TESTCODE:TODO:OLD# 
#TESTCODE:TODO:OLD# i0 = ASN1Integer ()
#TESTCODE:TODO:OLD# #CHANGED_TYPE# print 'Atom without seting string is', ''.join (map (lambda c:'%02x '%ord(c), str (i0))), 'length', len (i0)
#TESTCODE:TODO:OLD# print 'Atom int is', i0, '::', type (i0), 'with value', int (i0)
#TESTCODE:TODO:OLD# 
