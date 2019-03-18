# classes.py -- The various classes in the ASN.1 supportive hierarchy

import _quickder

from six.moves import intern

from quick_der import primitive
from quick_der.packstx import *


class ASN1Object (object):
	"""
	The ASN1Object is an abstract base class for all the value holders of ASN.1 data.  It has no value on its own.
	Data from subclasses is stored here, so subclasses can override the __getattr__() and __setattr__() methods,
	allowing obj.field notation. Subclasses are the following generic classes:
		 * `ASN1ConstructedType`
		 * `ASN1SequenceOf`
		 * `ASN1SetOf`
		 * `ASN1Atom`
	   The `asn2quickder` compiler creates further subclasses of these.
	   This means that all the data objects derived from unpacking DER
	   data are indirect subclasses of `ASN1Obejct`.
	"""

	_der_packer = None
	_recipe = None
	_numcursori = None

	def __init__ (self, derblob=None, jertokens=None, bindata=None, offset=0, der_packer=None, recipe=None, context=None):
		"""Initialise the current object; abstract classes require
		   parameters with typing information (der_packer, recipe,
		   numcursori).  Instance data may be supplied through bindata
		   and a possible offset, with a fallback to derblob that
		   will use the subclasses' _der_unpack() methods to form the
		   _bindata values.  If none of bindata, derblob, jertokens are
		   supplied, then an empty instance is delivered.  The optional
		   context defines the globals() map in which type references
		   should be resolved.
		"""
		# TODO:OLD# assert der_packer is not None or self._der_packer is not None, 'You or a class from asn2quickder must supply a DER_PACK_ sequence for use with Quick DER'
		assert (
		   bindata is not None and recipe is not None) or der_packer is not None or self._der_packer is not None, 'You or a class from asn2quickder must supply a DER_PACK_ sequence for use with Quick DER'
		assert recipe is not None or self._recipe is not None, 'You or a class from asn2quickder must supply a recipe for instantiating object structures'
		# TODO:OLD# assert bindata is not None or derblob is not None or self._numcursori is not None, 'When no binary data is supplied, you or a class from asn2quickder must supply how many DER cursors are used'
		# TODO:NEW:MAYBENOTNEEDED# assert self._numcursori is not None, 'You should always indicate how many values will be stored'
		assert context is not None or getattr (self, "_context",
		    None) is not None, 'You or a subclass definition should provide a context for symbol resolution'
		assert derblob is None or jertokens is None, 'Supply a derblob or jertokens, but not both'
		# Construct the type if so desired
		if der_packer is not None:
			self._der_packer = der_packer
		if recipe is not None:
			self._recipe = recipe
		if context is not None:
			self._context = context

		# Ensure presence of all typing data
		# Fill the instance data as supplied, or else make it empty
		if bindata:
			self._bindata = bindata
			self._offset = offset
			self.__init_bindata__ ()
		elif derblob:
			self._bindata = _quickder.der_unpack (self._der_packer, derblob, self._numcursori)
			self._offset = 0
			assert len (self._bindata) == self._numcursori, 'Wrong number of values returned from der_unpack ()'
			assert offset == 0, 'You supplied a derblob, so you cannot request any offset but 0'
			self.__init_bindata__ ()
		elif jertokens:
			# Start empty, then fill, then check
			self._offset = offset
			self._bindata = [None] * self._numcursori
			assert offset == 0, 'You supplied jertokens, so you cannot request any offset but 0'
			self._jer_unpack (jertokens, offset)
			#ALREADY_DONE# self.__init_bindata ()
		elif self._numcursori:
			self._bindata = [None] * self._numcursori
			self._offset = offset
			assert offset == 0, 'You supplied no initialisation data, so you cannot request any offset but 0'
			self.__init_bindata__ ()

	def __init_bindata__ (self):
		assert False, 'Expected __init_bindata__() method not found in ' + self.__class__.__name__

	def _jer_unpack (self):
		assert False, 'Expected _jer_unpack() method not found in ' + self.__class__.__name__

	def _jer_pack (self):
		assert False, 'Expected _jer_pack() method not found in ' + self.__class__.__name__


# The ASN1ConstructedType is a nested structure of named fields.
# Nesting instances share the bindata list structures, which they modify
# to retain sharing.  The reason for this is that the _der_pack() on the
# class must use changes made in the nested objects as well as the main one.

# SHARED IN LOWEST CLASS: ._recipe and ._der_packer
# STORED IN OBJECTS: ._fields, ._offset, ._bindata, ._numcursori

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
		(_NAMED, recp) = self._recipe
		self._fields = {}
		# Static recipe is generated from the ASN.1 grammar
		# Iterate over this recipe to form the instance data
		from quick_der import builder
		for (subfld, subrcp) in recp.items ():
			if type (subfld) != str:
				raise Exception ("ASN.1 recipe keys can only be strings")
			# Interned strings yield faster dictionary lookups
			# Field names in Python are always interned
			subfld = intern (subfld.replace ('-', '_'))
			self._fields [subfld] = self._offset  # fallback
			subval = builder.build_asn1 (self._context, subrcp,
						bindata=self._bindata,
						ofs=self._offset)
			if type (subval) == int:
				# Primitive: Index into _bindata; set in _fields
				#TODO# was += but build_asn1() adds in ofs too
				self._fields [subfld] = subval
			elif subval.__class__ == ASN1Atom:
				# The following moved into __init_bindata__ ():
				# self._bindata [self._offset] = subval
				# Native types may be assigned instead of subval
				pass
				print ('Not placing field {} subvalue :: {}'.format (subfld, type (subval)))
			elif isinstance (subval, ASN1Object):
				self._fields [subfld] = subval

	def _name2idx (self, name):
		while not name in self._fields:
			if name [:1] == '_':
				name = name [1:]
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
		   or a der_unpack(ClassName, derblob) or empty(ClassName)
		   call.  Return the bytes with the packed data.
		"""
		bindata = []
		for bd in self._bindata [self._offset:self._offset + self._numcursori]:
			# TODO# set, list, atomic...
			print ('bindata[] element is a {}'.format (type (bd)))
			if bd is not None and type (bd) != str:
				# Hope to map the value to DER without hints
				# TODO# Currently fails on ASN1Objects
				from quick_der import format
				bd = format.der_format (bd)
			bindata.append (bd)
		return _quickder.der_pack (self._der_packer, bindata)

	def _der_format (self):
		"""Format the current ASN1ConstructedType using DER notation,
		   but withhold the DER header consisting of the outer tag
		   and length.  This format is comparable to what is stored
		   in bindata array elements.  To be able to produce proper
		   DER, it needs some contextual information(specifically,
		   the tag to prefix before the body).
		"""
		packed = self._der_pack ()
		(tag, ilen, hlen) = _quickder.der_header (packed)
		return packed [hlen: hlen + ilen]

	def _jer_unpack (self, jertokens, offset):
		"""Parse JER tokens from an iterator and plant information in
		   the bindata subject to the given offset.  When an element
		   is added, build the underlying object and start again.

		   SEQUENCE in JER is an OBJECT with field names as keys.
		   (An ARRAY encoding instruction exists.)

		   SET in JER are an OBJECT with field names as keys.
		   (There is no ARRAY encoding instruction.)

		   CHOICE in JER is an OBJECT with one member, the variant
		   being selected by its field name.
		   (An UNWRAPPED encoding instruction is just the value.)

		   TODO: Why the "offset" parameter, not just self._offset?

		   TODO: Encoding instructions are not yet supported.

		   TODO: Consider wiping before and/or check for empty fields.
		"""
		jertokens.require_next ('{')
		(_NAMED,nmidx) = self._recipe
		self._fields = {}
		# Parse with a loop traversal for each "name" : value
		from quick_der import builder
		done = jertokens.lookahead () == '}'
		while not done:
			# Collect a string that serves as the field name
			# Interned strings yield faster dictionary lookups
			# Field names in Python are always interned
			tok = jertokens.require_next ('"')
			fld = intern (primitive.jer_parse_STRING (tok).replace ('-', '_'))
			if not nmidx.has_key (fld):
				raise jertokens.stxerr ('Unknown field name "%s"' % (fld,))
			self._fields [fld] = self._offset
			tok = jertokens.require_next (':')
			# Build field from subrecipe + jertokens; same object -> same offset
			subrcp = nmidx [fld]
			subval = builder.build_asn1 (self._context, subrcp,
							bindata=self._bindata,
							ofs=self._offset)
			if type (subval) == int:
				# Primitive: Index into _bindata; set in _fields
				#TODO# was += but build_asn1() adds in ofs too
				self._fields [subfld] = subval
			self._fields [fld] = subval
			# Beyond the value, we see if we should loop around
			tok = jertokens.require_next (',}')
			done = (tok == '}')
		# Parsing done
		#TODO# Consistency: all required / one choice / ...

	def _jer_pack (self, offset=0, indent=None):
		retval = '{ '
		comma = ''
		for (name, value) in self._fields.items ():
			#TODO# Too simplistic conversion, see __str__() below?
			newval = json.dumps (value)
			retval = retval + comma + name + ' : ' + newval
		retval = retval + ' }'
		return retval

	def __str__ (self):
		retval = '{\n	'
		comma = ''
		for (name, value) in self._fields.items ():
			if type (value) == int:
				value = self._bindata [value]
			if value is None:
				continue
			if isinstance (value, ASN1Atom) and value.get () is None:
				continue
			newval = str (value).replace ('\n', '\n	')
			retval = retval + comma + name + ' ' + newval
			comma = ',\n	'
		retval = retval + ' }'
		return retval


class ASN1SequenceOf (ASN1Object, list):
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
		(_SEQOF, allidx, subpck, subnum, subrcp) = self._recipe
		# TODO:DEBUG# print 'SEQUENCE OF from', self._offset, 'to', allidx, 'element recipe =', subrcp
		# TODO:DEBUG# print 'len(_bindata) =', len(self._bindata), '_offset =', self._offset, 'allidx =', allidx
		from quick_der import builder
		derblob = self._bindata [self._offset] or ''
		while len (derblob) > 0:
			# TODO:DEBUG# print 'Getting the header from ' + ' '.join (map (lambda x: x.encode ('hex'), derblob [:5])) + '...'
			(tag, ilen, hlen) = _quickder.der_header (derblob)
			if len (derblob) < hlen + ilen:
				raise Exception ('SEQUENCE OF elements must line up to a neat whole')
			subdta = derblob [:hlen + ilen]
			subcrs = _quickder.der_unpack (subpck, subdta, subnum)
			# TODO:ALLIDX# subval = builder.build_asn1 (self._context, subrcp, subcrs, allidx)
			subval = builder.build_asn1 (self._context, subrcp,
							bindata=subcrs,
							ofs=0)
			self.append (subval)
			derblob = derblob [hlen + ilen:]
		self._bindata [self._offset] = self

	def _der_pack (self):
		"""Return the result of the `der_pack ()` operation on this
		   element.
		"""
		return primitive.der_prefixhead (DER_PACK_ENTER | DER_TAG_SEQUENCE,
		                                 self._der_format ())

	def _der_format (self):
		"""Format the current ASN1SequenceOf using DER notation,
		   but withhold the DER header consisting of the outer tag
		   and length.  This format is comparable to what is stored
		   in bindata array elements.  To be able to produce proper
		   DER, it needs some contextual information (specifically,
		   the tag to prefix before the body).
		"""
		return ''.join ([elem._der_pack () for elem in self])

	def _jer_unpack (self, jertokens, offset):
		"""Parse JSON tokens for a SEQUENCE OF and construct the
		   resulting elements, as well as the element class for
		   each entry.

		   SEQUENCE OF in JER is an ARRAY with member JSON values.
		"""
		jertokens.require_next ('[')
		(_SEQOF, allidx, subpck, subnum, subrcp) = recipe
		# Parse with a loop traversal for each value
		from quick_der import builder
		done = jertokens.lookahead () == ']'
		while not done:
			# Build value from subrecipe + jertokens; fresh offset counting
			subval = builder.build_asn1 (self._context, subrcp,
							bindata=None,
							ofs=0)
			subval._jer_unpack (jertokens, 0)
			self.append (val)
			# Beyond the value, we see if we should loop around
			tok = jertokens.require_next (',]')
			done = (tok == ']')
		# Parsing done
		self._bindata [self._offset] = self

	def _jer_pack (self, offset=0, indent=None):
		raise NotImplementedError ('_jer_pack()')

	def __str__ (self):
		entries = ',\n'.join ([str(x) for x in self])
		entries.replace ('\n', '\n	')
		return 'SEQUENCE { ' + entries + ' }'


class ASN1SetOf (ASN1Object, set):
	"""An ASN.1 representation for a SET OF other ASN1Object values.

	   The instances of this class can be manipulated just like Python's
	   native set type.

	   TODO: Need to _der_pack() and get the result back into a context.
	"""

	_der_packer = chr(DER_PACK_STORE | DER_TAG_SET) + chr(DER_PACK_END)
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
		(_SETOF, allidx, subpck, subnum, subrcp) = self._recipe
		# TODO:DEBUG# print 'SET OF from', self._offset, 'to', allidx, 'element recipe =', subrcp
		# TODO:DEBUG# print 'len (_bindata) =', len (self._bindata), '_offset =', self._offset, 'allidx =', allidx
		derblob = self._bindata [self._offset] or ''
		from quick_der import builder
		while len (derblob) > 0:
			(tag, ilen, hlen) = _quickder.der_header (derblob)
			if len (derblob) < hlen + ilen:
				raise Exception ('SET OF elements must line up to a neat whole')
			subdta = derblob [:hlen + ilen]
			subcrs = _quickder.der_unpack (subpck, subdta, subnum)
			# TODO:ALLIDX# subval = builder.build_asn1 (self._context, subrcp, subcrs, allidx)
			subval = builder.build_asn1 (self._context, subrcp,
							bindata=subcrs,
							ofs=0)
			self.add (subval)
			derblob = derblob [hlen + ilen:]
		self._bindata [self._offset] = self

	def _der_pack (self):
		"""Return the result of the `der_pack ()` operation on this
		   element.
		"""
		return primitive.der_prefixhead (DER_PACK_ENTER | DER_TAG_SET,
		                                 self._der_format ())

	def _der_format (self):
		"""Format the current ASN1SetOf using DER notation,
		   but withhold the DER header consisting of the outer tag
		   and length.  This format is comparable to what is stored
		   in bindata array elements.  To be able to produce proper
		   DER, it needs some contextual information (specifically,
		   the tag to prefix before the body).
		"""
		return ''.join ([elem._der_pack () for elem in self])

	def _jer_unpack (self, jertokens, offset):
		"""Parse JSON tokens for a SET OF and construct the
		   resulting elements, as well as the element class for
		   each entry.

		   SET OF in JER is an ARRAY with member JSON values.
		"""
		jertokens.require_next ('[')
		(_SETOF, allidx, subpck, subnum, subrcp) = recipe
		self._bindata [offset + allidx] = set ()
		# Parse with a loop traversal for each value
		done = jertokens.lookahead () == ']'
		from quick_der import builder
		while not done:
			# Build value from subrecipe + jertokens; fresh offset counting
			subval = builder.build_asn1 (self._context, subrcp,
							bindata=None,
							ofs=0)
			subval._jer_unpack (jertokens, 0)
			self.add (subval)
			# Beyond the value, we see if we should loop around
			tok = jertokens.require_next (',]')
			done = (tok == ']')
		# Parsing done
		self._bindata [self._offset] = self

	def _jer_pack (self, offset=0, indent=None):
		raise NotImplementedError ('_jer_pack()')

	def __str__ (self):
		entries = ',\n'.join ([str (x) for x in self])
		entries.replace ('\n', '\n	')
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
	_jer_parse_1 = None
	_jer_parse_re = None
	_jer_parse_fn = primitive.jer_parse_STRING
	_jer_format_fn = primitive.jer_format_STRING

	# The following lists the data types that can be represented in an
	# ASN1Atom, but that might also find another format more suited to
	# their needs.  Each mapping finds a function that produces a more
	# suitable form.  This form is then better used instead of the
	# default # ASN1Atom representation, which is like a contained string
	# with get() and set() methods to see and change it.  The functions
	# mapped to interpret DER content and map it to a native type.
	_direct_data_map = {
		DER_TAG_BOOLEAN: primitive.der_parse_BOOLEAN,
		DER_TAG_INTEGER: primitive.der_parse_INTEGER,
		DER_TAG_BITSTRING: primitive.der_parse_BITSTRING,
		DER_TAG_OCTETSTRING: primitive.der_parse_STRING,
		# DEFAULT# DER_TAG_NULL: ASN1Atom,
		DER_TAG_OID: primitive.der_parse_OID,
		# DEFAULT# DER_TAG_OBJECT_DESCRIPTOR: ASN1Atom,
		# DEFAULT# DER_TAG_EXTERNAL:  ASN1Atom,
		DER_TAG_REAL: primitive.der_parse_REAL,
		DER_TAG_ENUMERATED: primitive.der_parse_INTEGER,  # TODO# der2enum???
		# DEFAULT# DER_TAG_EMBEDDED_PDV: ASN1Atom,
		DER_TAG_UTF8STRING: primitive.der_parse_STRING,
		DER_TAG_RELATIVE_OID: primitive.der_parse_RELATIVE_OID,
		DER_TAG_NUMERICSTRING: primitive.der_parse_STRING,
		DER_TAG_PRINTABLESTRING: primitive.der_parse_STRING,
		DER_TAG_TELETEXSTRING: primitive.der_parse_STRING,
		DER_TAG_VIDEOTEXSTRING: primitive.der_parse_STRING,
		DER_TAG_IA5STRING: primitive.der_parse_STRING,
		DER_TAG_UTCTIME: primitive.der_parse_UTCTIME,
		DER_TAG_GENERALIZEDTIME: primitive.der_parse_GENERALIZEDTIME,
		DER_TAG_GRAPHICSTRING: primitive.der_parse_STRING,
		DER_TAG_VISIBLESTRING: primitive.der_parse_STRING,
		DER_TAG_GENERALSTRING: primitive.der_parse_STRING,
		DER_TAG_UNIVERSALSTRING: primitive.der_parse_STRING,
		DER_TAG_CHARACTERSTRING: primitive.der_parse_STRING,
		DER_TAG_BMPSTRING: primitive.der_parse_STRING,
	}

	# The tags in the _direct_data_replace set are replaced in the
	# _bindata [_offset] entry, so this is no longer a binary string
	# but rather the current ASN1Atom subclass
	_direct_data_replace = {
		DER_TAG_BOOLEAN,
		DER_TAG_BITSTRING,
		DER_TAG_OID,
		DER_TAG_ENUMERATED,
		DER_TAG_RELATIVE_OID,
		DER_TAG_UTCTIME,
		DER_TAG_GENERALIZEDTIME,
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
		self._value = self._bindata [self._offset]
		mytag = ord (self._der_packer [0]) & DER_PACK_MATCHBITS
		if mytag in self._direct_data_map:
			mapfun = self._direct_data_map [mytag]
			if self._bindata [self._offset] is None:
				pass  # Keep the None value in _bindata [_offset]
			else:
				mapped_value = mapfun (self._value)
				if mytag in self._direct_data_replace:
					# Replace the _value
					self._value = mapped_value
					# Replace the _bindata [_offset]
					self._bindata [self._offset] = self
		else:
			pass  # Keep binary string in _bindata [_offset]
			#	   # Keep binary string in _value: self is usable

	def get (self):
		return self._value

	def set (self, derblob):
		if type (derblob) == str:
			self._value = derblob
		else:
			raise ValueError ('ASN1Atom.set() only accepts derblob strings')

	# OLD#	 def __str__ (self):
	# OLD#		 if self._value is not None:
	# OLD#			 return self._value
	# OLD#		 else:
	# OLD#			 return ''

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = "'" + self._der_format ().encode ('hex') + "'H"
		else:
			retval = 'None'
		return retval

	def __len__ (self):
		if self._value:
			# A bit wasteful to compute the DER format for len
			return len (self._der_format ())
		else:
			return 0

	def _der_pack (self):
		"""Return the result of the `der_pack()` operation on this
		   element.
		"""
		return primitive.der_prefixhead (self._der_packer [0],
		                                 self._der_format ())

	def _der_format (self):
		"""Format the current ASN1Atom using DER notation,
		   but withhold the DER header consisting of the outer tag
		   and length.  This format is comparable to what is stored
		   in bindata array elements.  To be able to produce proper
		   DER, it needs some contextual information (specifically,
		   the tag to prefix before the body).
		"""
		return self._bindata [self._offset]

	def _jer_unpack (self, jertokens, offset):
		"""Generic JER unpacker for all ASN1Atom values.
		   Uses _jer_parse_1 as a list of first characters;
		   Uses _jer_parse_re as a regex for the next value;
		   uses _jer_parse_fn as a function to parse the value;
		   assumes _jer_format_fn to represent the value.
		"""
		tok = jertokens.require_next (self._jer_parse_1)
		if self._jer_parse_re is not None:
			if self._jer_parse_re.match (tok) is None:
				cls = self.__class__.__name__
				if cls [:4] == 'ASN1':
					cls = cls [4:].upper ()
				raise jertokens.stxerr ('Expected %s, got "%s"' % (cls,tok) )
		self._bindata [offset] = self._jer_parse_fn (tok)

	def _jer_pack (self):
		"""Generic JER packer for all ASN1Atom values.
		   Uses _jer_format_fn as a function to represent the value;
		   assumes _jer_parse_fn to parse the value;
		   assumes _jer_parse_re as a regex for the value.
		"""
		value = self._bindata [offset]
		return self._jer_format_fn (value)


class ASN1Boolean (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_BOOLEAN) + chr(DER_PACK_END)

	_jer_parse_1 = 'tf'
	_jer_parse_fn = primitive.jer_parse_BOOLEAN
	_jer_format_fn = primitive.jer_format_BOOLEAN

	def __str__ (self):
		if self.get ():
			return 'TRUE'
		else:
			return 'FALSE'

	def _der_format (self):
		return primitive.der_format_BOOLEAN (self.get ())


class ASN1Integer (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_INTEGER) + chr(DER_PACK_END)

	_jer_parse_1 = '-0123456789'
	_jer_parse_re = re.compile ('^-?(?:0|[1-9][0-9]*)$')
	_jer_parse_fn = primitive.jer_parse_INTEGER
	_jer_format_fn = primitive.jer_format_INTEGER

	def get (self):
		val = super (ASN1Integer, self).get ()
		if val is not None:
			val = primitive.der_parse_INTEGER (val)
		return val

	def set (self, val):
		if val is not None:
			val = primitive.der_format_INTEGER (val)
		super (ASN1Integer, self).set (val)

	def __int__ (self):
		return self.get () or 0

	def __str__ (self):
		return str (self.__int__ ())

	def _der_format (self):
		return primitive.der_format_INTEGER (self.get ())


class ASN1BitString (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_BITSTRING) + chr(DER_PACK_END)

	_re_jer = {
		'length': re.compile ('^[1-9][0-9]*$'),
		'value':  re.compile ('^([0-9a-fA-F][0-9a-fA-F])*$')
	}

	def test (self, bit):
		#TODO# This does not seem to work?!?
		return bit in self._bindata [self._offset]

	def set (self, bit):
		#TODO# This does not seem to work?!?
		self._bindata [self._offset].add (bit)

	def clear (self, bit):
		#TODO# This does not seem to work?!?
		self._bindata [self._offset].remove (bit)

	def _der_format (self):
		return primitive.der_format_BITSTRING (self.get ())

	def _jer_unpack (self, jertokens, offset):
		"""Parse a JER value for a BITSTRING.  Since size constraints
		   are not incorporated, we always treat a BITSTRING as a
		   variable-sized struct.  This is represented in an object
		   with a "value" and "length" member; the former holding a
		   HEX encoding for the bytes expressing each bit; the latter
		   holding the number of bits.  There may be up to 7 extra
		   bits, which must all be zero.
		"""
		jertokens.require_next ('{')
		out = { 'value': None, 'length': None }
		req = { 'value': '"', 'length': '0123456789' }
		while True:
			# Accept one of the attributes (in any order)
			attr = jertokens.parse_next ()
			if not out.has_key (attr):
				raise jertokens.stxerr ('BITSTRING holds only "value" and "length"')
			if out [attr] is not None:
				raise jertokens.stxerr ('BITSTRING only needs one "%s"' % (attr,))
			# Skip ahead to the value
			jertokens.require_next (':')
			val = jertokens.require_next (req [attr])
			if ASN1BitString._re_jer [attr].match (val) is None:
				raise jertokens.stxerr ('BITSTRING "value" or "length" is invalid')
			out [attr] = val
			# End the loop or go for another round
			if None not in out.values ():
				break
			jertokens.require_next (',')
		jertokens.require_next ('}')
		numbits = int (out ['length'])
		if numbits != 8 * len (out ['value']):
			# BIT STRINGS are only supported with multiple-of-8 bit counts
			raise jertokens.stxerr ('BITSTRING length seems off')
		self._bindata [offset] = out ['value'].decode ('hex')

	def _jer_pack (self, offset=0, indent=None):
		fmt = '{ "length" : %d, "value": "%s" }'
		return fmt % (len (self._bindata [offset]),
				self._bindata [offset].encode ('hex'))

	def _jer_pack (self, offset=0, indent=None):
		raise NotImplementedError ('_jer_pack()')


class ASN1OctetString (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_OCTETSTRING) + chr(DER_PACK_END)

	_jer_parse_1 = '"'
	_jer_parse_re = re.compile ('^([0-9a-fA-F][0-9a-fA-F])*$')
	_jer_parse_fn = primitive.jer_parse_HEXSTRING
	_jer_format_fn = primitive.jer_format_HEXSTRING

	def _encode_BASE64 (self):
		self._jer_parse_re = re.compile ('^[0-9a-zA-Z]*=*$')
		self._jer_parse_fn = primitive.jer_parse_BASE64STRING
		self._jer_format_fn = primitive.jer_format_BASE64STRING


class ASN1Null (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_NULL) + chr(DER_PACK_END)

	_jer_parse_1 = 'n'
	_jer_parse_fn = primitive.jer_parse_NULL
	_jer_format_fn = primitive.jer_format_NULL

	def __str__ (self):
		return 'NULL'


class ASN1OID (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_OID) + chr(DER_PACK_END)

	_jer_parse_1 = '123456789'
	_jer_parse_re = re.compile ('^"[1-9][0-9]*([.][1-9][0-9]*)*$"')
	_jer_parse_fn = primitive.jer_parse_OID
	_jer_format_fn = primitive.jer_format_OID

	def __str__ (self):
		oidstr = primitive.der_parse_OID (self.get ())
		return '{ ' + oidstr.replace ('.', ' ') + ' }'

	def _der_format (self):
		return primitive.der_format_OID (self.get ())


class ASN1Real (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_REAL) + chr(DER_PACK_END)

	_jer_parse_1 = '-0123456789'
	_jer_parse_re = re.compile ('^("(-0|-INF|INF|NaN)"|-?[0-9].*)$')
	_jer_parse_fn = primitive.jer_parse_REAL
	_jer_format_fn = primitive.jer_format_REAL

	def _der_format (self):
		return primitive.der_format_REAL (self.get ())


class ASN1Enumerated (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_ENUMERATED) + chr(DER_PACK_END)

	def _der_format (self):
		return primitive.der_format_INTEGER (self.get ())


class ASN1UTF8String (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_UTF8STRING) + chr(DER_PACK_END)

	_jer_parse_1 = '"'
	_jer_parse_fn = primitive.jer_parse_STRING
	_jer_format_fn = primitive.jer_format_STRING

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1RelativeOID (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_RELATIVE_OID) + chr(DER_PACK_END)

	def _der_format (self):
		return primitive.der_format_RELATIVE_OID (self.get ())


class ASN1NumericString (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_NUMERICSTRING) + chr(DER_PACK_END)

	_jer_parse_1 = '"'
	_jer_parse_fn = primitive.jer_parse_STRING
	_jer_format_fn = primitive.jer_format_STRING

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1PrintableString (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_PRINTABLESTRING) + chr(DER_PACK_END)

	_jer_parse_1 = '"'
	_jer_parse_fn = primitive.jer_parse_STRING
	_jer_format_fn = primitive.jer_format_STRING

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1TeletexString (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_TELETEXSTRING) + chr(DER_PACK_END)

	_jer_parse_1 = '"'
	_jer_parse_re = re.compile ('^([0-9a-fA-F][0-9a-fA-F])*$')
	_jer_parse_fn = primitive.jer_parse_HEXSTRING
	_jer_format_fn = primitive.jer_format_HEXSTRING

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1VideotexString (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_VIDEOTEXSTRING) + chr(DER_PACK_END)

	_jer_parse_1 = '"'
	_jer_parse_re = re.compile ('^([0-9a-fA-F][0-9a-fA-F])*$')
	_jer_parse_fn = primitive.jer_parse_HEXSTRING
	_jer_format_fn = primitive.jer_format_HEXSTRING

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1IA5String (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_IA5STRING) + chr(DER_PACK_END)

	_jer_parse_1 = '"'
	_jer_parse_fn = primitive.jer_parse_STRING
	_jer_format_fn = primitive.jer_format_STRING

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1UTCTime (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_UTCTIME) + chr(DER_PACK_END)

	_jer_parse_1 = '"'
	_jer_parse_fn = primitive.jer_parse_STRING
	_jer_format_fn = primitive.jer_format_STRING

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self._der_format () + '"'
		else:
			retval = 'None'
		return retval

	def _der_format (self):
		return primitive.der_format_UTCTIME (self.get ())


class ASN1GeneralizedTime (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_GENERALIZEDTIME) + chr(DER_PACK_END)

	_jer_parse_1 = '"'
	_jer_parse_fn = primitive.jer_parse_STRING
	_jer_format_fn = primitive.jer_format_STRING

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self._der_format () + '"'
		else:
			retval = 'None'
		return retval

	def _der_format (self):
		return primitive.der_format_GENERALIZEDTIME (self.get ())


class ASN1GraphicString (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_GRAPHICSTRING) + chr(DER_PACK_END)

	_jer_parse_1 = '"'
	_jer_parse_re = re.compile ('^([0-9a-fA-F][0-9a-fA-F])*$')
	_jer_parse_fn = primitive.jer_parse_HEXSTRING
	_jer_format_fn = primitive.jer_format_HEXSTRING


class ASN1VisibleString (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_VISIBLESTRING) + chr(DER_PACK_END)

	_jer_parse_1 = '"'
	_jer_parse_fn = primitive.jer_parse_STRING
	_jer_format_fn = primitive.jer_format_STRING

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1GeneralString (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_GENERALSTRING) + chr(DER_PACK_END)

	_jer_parse_1 = '"'
	_jer_parse_re = re.compile ('^([0-9a-fA-F][0-9a-fA-F])*$')
	_jer_parse_fn = primitive.jer_parse_HEXSTRING
	_jer_format_fn = primitive.jer_format_HEXSTRING

	def __str__ (self):
		retval = self.get ()
		if retval:
			retval = '"' + self.get () + '"'
		else:
			retval = 'None'
		return retval


class ASN1UniversalString (ASN1Atom):
	_der_packer = chr(DER_PACK_STORE | DER_TAG_UNIVERSALSTRING) + chr(DER_PACK_END)

	_jer_parse_1 = '"'
	_jer_parse_fn = primitive.jer_parse_STRING
	_jer_format_fn = primitive.jer_format_STRING

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
	_jer_tokens = None

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
		assert self._class is None, 'ANY type has already been made concrete'
		self._class = cls
		self._value = cls (recipe=cls._recipe,
		                   der_packer=cls._der_packer,
		                   derblob=self._bindata [self._offset],
		                   jertokens=_jer_tokens,
		                   offset=0,
		                   context=cls._context)

	def der_pack (self):
		from quick_der import format
		return format.der_pack (self._value, cls=self._class)

	def _jer_unpack (self, jertokens, offset):
		"""JER tokens for ANY cannot be processed before the
		   class has been set with set_class().  However, what
		   we can assume is that a single value will be parsed
		   later on, and that we can store that one token for
		   future use.  Of course, if the class has been set,
		   processing can commence immediately.
		"""
		if self._class is None:
			self._jer_tokens = jer.SubTokenizer (jertokens)
		else:
			self._value._jer_unpack (jertokens, 0)

	def _jer_pack (self, offset=0, indent=None):
		return self._value._jer_pack (offset, indent)


