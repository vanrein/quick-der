# classes.py -- The various classes in the ASN.1 supportive hierarchy


import _quickder

from packstx import *

import primitive
import builder


if not 'intern' in dir (globals () ['__builtins__']):
	try:
		from sys import intern
	except:
		intern = lambda s: s


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
		if self._recipe [0] != '_NAMED':
			import sys
			sys.exit (1)
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
			subval = builder.build_asn1 (self._context, subrcp, self._bindata, self._offset)
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
			if type (idx) == int:
				self._bindata [idx] = val
			else:
				idx.set (val)
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

	def __dir__ (self):
		"""Explicitly list the contents of the ASN1ConstructedType.
		   Not sure why, but dir() ends in an infinite loop, probably
		   due to the __getattr__ definition in this class.  Setting
		   an explicit __dir__() method helps.
		"""
		return ['_der_packer','_numcursori','_recipe','_context','_bindata','_offset','_fields'] + self._fields.keys ()

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
		derblob = self._bindata [self._offset] or ''
		while len (derblob) > 0:
			#TODO:DEBUG# print 'Getting the header from ' + ' '.join (map (lambda x: x.encode ('hex'), derblob [:5])) + '...'
			(tag,ilen,hlen) = _quickder.der_header (derblob)
			if len (derblob) < hlen+ilen:
				raise Exception ('SEQUENCE OF elements must line up to a neat whole')
			subdta = derblob [:hlen+ilen]
			subcrs = _quickder.der_unpack (subpck,subdta,subnum)
			#TODO:ALLIDX# subval = builder.build_asn1 (self._context, subrcp, subcrs, allidx)
			subval = builder.build_asn1 (self._context, subrcp, subcrs, 0)
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
		derblob = self._bindata [self._offset] or ''
		while len (derblob) > 0:
			(tag,ilen,hlen) = _quickder.der_header (derblob)
			if len (derblob) < hlen+ilen:
				raise Exception ('SET OF elements must line up to a neat whole')
			subdta = derblob [:hlen+ilen]
			subcrs = _quickder.der_unpack (subpck,subdta,subnum)
			#TODO:ALLIDX# subval = builder.build_asn1 (self._context, subrcp, subcrs, allidx)
			subval = builder.build_asn1 (self._context, subrcp, subcrs, 0)
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
		DER_TAG_BOOLEAN: primitive.der_unpack_BOOLEAN,
		DER_TAG_INTEGER: primitive.der_unpack_INTEGER,
		DER_TAG_BITSTRING: primitive.der_unpack_BITSTRING,
		DER_TAG_OCTETSTRING: primitive.der_unpack_STRING,
		#DEFAULT# DER_TAG_NULL: ASN1Atom,
		DER_TAG_OID: primitive.der_unpack_OID,
		#DEFAULT# DER_TAG_OBJECT_DESCRIPTOR: ASN1Atom,
		#DEFAULT# DER_TAG_EXTERNAL:  ASN1Atom,
		DER_TAG_REAL: primitive.der_unpack_REAL,
		DER_TAG_ENUMERATED: primitive.der_unpack_INTEGER,	#TODO# der2enum???
		#DEFAULT# DER_TAG_EMBEDDED_PDV: ASN1Atom,
		DER_TAG_UTF8STRING: primitive.der_unpack_STRING,
		DER_TAG_RELATIVE_OID: primitive.der_unpack_RELATIVE_OID,
		DER_TAG_NUMERICSTRING: primitive.der_unpack_STRING,
		DER_TAG_PRINTABLESTRING: primitive.der_unpack_STRING,
		DER_TAG_TELETEXSTRING: primitive.der_unpack_STRING,
		DER_TAG_VIDEOTEXSTRING: primitive.der_unpack_STRING,
		DER_TAG_IA5STRING: primitive.der_unpack_STRING,
		DER_TAG_UTCTIME: primitive.der_unpack_UTCTIME,
		DER_TAG_GENERALIZEDTIME: primitive.der_unpack_GENERALIZEDTIME,
		DER_TAG_GRAPHICSTRING: primitive.der_unpack_STRING,
		DER_TAG_VISIBLESTRING: primitive.der_unpack_STRING,
		DER_TAG_GENERALSTRING: primitive.der_unpack_STRING,
		DER_TAG_UNIVERSALSTRING: primitive.der_unpack_STRING,
		DER_TAG_CHARACTERSTRING: primitive.der_unpack_STRING,
		DER_TAG_BMPSTRING: primitive.der_unpack_STRING,
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

	def get (self):
		val = super (ASN1Integer,self).get ()
		if val is not None:
			val = primitive.der_unpack_INTEGER (val)
		return val

	def set (self, val):
		if val is not None:
			val = primitive.der_pack_INTEGER (val)
		super (ASN1Integer, self).set (val)

	def __int__ (self):
		return (self.get () or 0)

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
		oidstr = primitive.der_unpack_OID (self.get ())
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


