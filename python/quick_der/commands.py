# commands.py -- Externally callable commands (from script wrappers)
#
# From: Rick van Rein <rick@openfortress.nl>


def der2ber (asn1class, derblob):
	"""This is trivial!  DER is a subset of BER and
	   so this function is an identity.  You can use
	   it for symmetry, though.
	"""
	assert issubclass (asn1class, ASN1Object)
	return derblob


def ber2der (asn1class, berblob):
	"""Our Quick DER parser accepts (most of) BER, and
	   so we can parse and reproduce the information
	   to canonicalise it in a DER format.  We do need
	   to be exhaustive; SEQUENCE OF, SET OF and ANY
	   all need to be expanded.
	   
	   TODO: This is not automatic for ANY...
	"""
	assert issubclass (asn1class, ASN1Object)
	mid = asn1class (derblob=berblob)
	return mid._der_pack ()


def jer2der (asn1class, jertokens):
	assert issubclass (asn1class, ASN1Object)
	mid = asn1class (jertokens=jertokens)
	return mid._der_pack ()


jer2ber = jer2der


def ber2jer (asn1class, berblob):
	assert issubclass (asn1class, ASN1Object)
	mid = asn1class (derblob=berblob)
	return mid._jer_pack ()


der2jer = ber2jer


