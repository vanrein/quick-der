class ASN1Object (object):

	def __init__ (self, bindata='', ofslen=[], structure={}):
		ASN1Object.bindata = bindata
		ASN1Object.ofslen = ofslen
		ASN1Object.structure = structure
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
		ASN1Object.ofslen [ASN1Object.structure [name]] = ( len(ASN1Object.bindata), len (val) )
		ASN1Object.bindata = ASN1Object.bindata + val

	def __getattr__ (self, name):
		if not ASN1Object.structure.has_key (name):
			raise AttributeError (name)
		idx = ASN1Object.structure [name]
		if idx < len (ASN1Object.ofslen):
			(ofs,siz) = ASN1Object.ofslen [ASN1Object.structure [name]]
		else:
			(ofs,siz) = (0,0)
		return ASN1Object.bindata [ofs:ofs+siz]


# class LDAPMessage (ASN1Object):
if True:

	bindata = 'Hello World'
	ofslen = [ (0,5), (6,5) ]
	structure = { 'hello': 0, 'world': 1 }

	# def unpack (self):
	# 	return ASN1Object (bindata=self.bindata, ofslen=self.ofslen, structure=self.structure)

	def unpack ():
		return ASN1Object (bindata=bindata, ofslen=ofslen, structure=structure)


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

