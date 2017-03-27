# api.py represents the general access point to quick_der


# We need three methods with Python wrapping in C plugin module _quickder:
# der_pack() and der_unpack() with proper memory handling, plus der_header()
#  * Arrays of dercursor are passed as arrays of (copied) Python strings
#  * Bindata is passed as Python strings
import _quickder

# Import the DER_TAG_xxx and DER_PACK_xxx symbol definitions
from packstx import *

# Import primvite der_pack_TYPE and der_unpack_TYPE routines
from primitive import *

# Import ASN.1 supportive classes ASN1xxx
from classes import *

# Import the build_asn1() routine
from builder import *

