#! /usr/bin/env python

import sys
import bagels
import donuts

print( "\n".join(sys.path) )
print( "\n".join(bagels.flavors()) )
print( "\n".join(donuts.flavors) )
