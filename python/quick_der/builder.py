# builder.py -- home of the build_asn1() routine
#
# Future versions may also host der_pack(), der_unpack() or similar


import classes


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
		return classes.ASN1ConstructedType (
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
			cls = classes.ASN1SequenceOf
		else:
			cls = classes.ASN1SetOf
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
		instme = None
		while type (recipe) == tuple and recipe [0] == '_TYPTR':
			(_TYPTR,[subcls],subofs) = recipe
			ofs += subofs
			if type (subcls) == str:
				#TODO# Try to remove these, since we now generate it?
				if subcls [:5] == '_api.':
					context = context ['_api'].__dict__
					subcls = subcls [5:]
				elif subcls [:4] == 'ASN1':
					context = context ['_api'].__dict__
				#TODO# End try-to-remove-these
				subcls = context [subcls]	# lazy link
				recipe [1] [0] = subcls		# memorise
			assert issubclass (subcls, classes.ASN1Object), 'Recipe ' + repr (recipe) + ' does not subclass ASN1Object'
			assert type (subofs) == int, 'Recipe ' + repr (recipe) + ' does not have an integer sub-offset'
			if instme is None:
				instme = subcls
			recipe = subcls._recipe
		return instme (
					recipe = subcls._recipe,
					der_packer = subcls._der_packer,
					bindata = bindata,
					offset = ofs,
					context = context )
	else:
		assert False, 'Unknown recipe tag ' + str (recipe [0])
