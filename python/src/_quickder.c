/* Custom wrappers for Python/C interface to Quick DER.
 *
 * The Quick DER support in Python defines packages to represent ASN.1 specs,
 * classes to represent types and their DER unpackers, and instances to
 * represent parsed data.  Instances may be edited to accommodate future
 * packing or unpacking.
 *
 * The routines below make der_pack() and der_unpack() operations callable
 * from Python.  This is usually done from Python code generated by
 * asn2quickder to accommodate the ASN.1 input specifications.
 *
 * The resulting code does not present packer coding explicitly to the
 * end user, but wraps it inside appropriately named classes.  Under these
 * considerations, it may be expected that the resulting code is safe.
 *
 * It is also possible to manually define wrappers, but in that case a risk
 * of crashing the C backend arises when structures are not properly sized
 * or when their offsets are out of range.  We may be able to fix that in a
 * future version.
 *
 * The routines currently provide no parsing support, such as mappings for
 * INTEGER values.  We may be able to provide for such helps in a future
 * version.
 *
 * The code below allocates DER structures on the stack, assuming that sizes
 * are kept modest.  This may crash the program when not cared for.  We may
 * want or need to change that through malloc() in a future version.
 *
 * From: Rick van Rein <rick@openfortress.nl>
 */


#include <Python.h>

#include <arpa2/quick-der.h>


/* _quickder.der_unpack (pck, bin, numcursori) -> cursori */
static PyObject *quickder_unpack (PyObject *self, PyObject *args) {
	char *pck;
	int pcklen;
	char *bin;
	int binlen;
	int numcursori;
	//
	// Parse the arguments
	PyObject *retval = NULL;
	if (!PyArg_ParseTuple (args, "s#s#i", &pck, &pcklen, &bin, &binlen, &numcursori)) {
		return NULL;
	}
	//
	// Allocate the dercursor array
	dercursor cursori [numcursori];
	dercursor binput;
	binput.derptr = (uint8_t *)bin;
	binput.derlen = binlen;
	if (der_unpack (&binput, (derwalk *)pck, cursori, 1)) {
		PyErr_SetFromErrno (PyExc_OSError);
		return NULL;
	}
	//
	// Construct the structure of cursori to be returned
	retval = PyList_New (numcursori);
	if (retval == NULL) {
		return NULL;
	}
	while (numcursori-- > 0) {
		PyObject *elem;
		if (cursori [numcursori].derptr == NULL) {
			Py_INCREF (Py_None);
			elem = Py_None;
		} else {


			#if PY_MAJOR_VERSION >= 3
			elem = PyUnicode_FromStringAndSize ((char *)cursori [numcursori].derptr, cursori [numcursori].derlen);
			#else
			elem = PyString_FromStringAndSize ((char *)cursori [numcursori].derptr, cursori [numcursori].derlen);
			#endif


			if (elem == NULL) {
				Py_DECREF (retval); // not returned, so discard
				return NULL;
			}
		}
		if (PyList_SetItem (retval, numcursori, elem)) {
			Py_DECREF (elem);	// not inserted, so discard
			Py_DECREF (retval);	// not returned, so discard
			return NULL;
		}
	}
	//
	// Cleanup and return
	return retval;
}


/* _quickder.der_pack (pck, crsvals) -> bin */
static PyObject *quickder_pack (PyObject *self, PyObject *args) {
	char *pck;
	int pcklen;
	PyObject *bins;
	Py_ssize_t binslen;
	PyObject *retval = NULL;
	//
	// Parse arguments, generally
	if (!PyArg_ParseTuple (args, "s#O", &pck, &pcklen, &bins)) {
		return NULL;
	}
	// "bins" is refct'd by "args", which is held during this function call
	if (!PyList_Check (bins)) {
		return NULL;
	}
	binslen = PyList_Size (bins);
	//
	// Collect cursori, the dercursor array for der_pack()
	dercursor cursori [binslen];
	while (binslen-- > 0) {
		PyObject *elem = PyList_GetItem (bins, binslen);
		// "elem" is a borrowed reference; theory of race condition?!?
		if (elem == Py_None) {
			memset (&cursori [binslen], 0, sizeof (*cursori));

		#if PY_MAJOR_VERSION >= 3
		} else if (PyUnicode_Check (elem)) {
		#else
		} else if (PyString_Check (elem)) {
		#endif
			char *buf;
			Py_ssize_t buflen;
			//TODO// Retval from following call?  Can it go wrong?
			#if PY_MAJOR_VERSION >= 3
			PyBytes_AsStringAndSize (elem, &buf, &buflen);
			#else
			PyString_AsStringAndSize (elem, &buf, &buflen);
			#endif

			cursori [binslen].derptr = (uint8_t *)buf;
			cursori [binslen].derlen = buflen;
		} else {
			return NULL;
		}
	}
	//
	// Determine the length of the packed string
	ssize_t packedlen = der_pack ((derwalk *)pck, cursori, NULL);
	if (packedlen < 0) {
		PyErr_SetFromErrno (PyExc_OSError);
		return NULL;
	}
	uint8_t packed [packedlen];
	der_pack ((derwalk *)pck, cursori, packed + packedlen);

	#if PY_MAJOR_VERSION >= 3
	retval = PyUnicode_FromStringAndSize ((char *)packed, packedlen);
	#else
	retval = PyString_FromStringAndSize ((char *)packed, packedlen);
	#endif


	if (retval == NULL) {
		return NULL;
	}
	// "retval" is a new reference, with a copy of packed
	//
	// Cleanup and return
	return retval;
}


/* _quickder.der_header (cursor) -> (tag, len, hlen) */
static PyObject *quickder_header (PyObject *self, PyObject *args) {
	char *buf;
	Py_ssize_t buflen;
	dercursor crs;
	PyObject *retval = NULL;
	//
	// Verify and obtain invocation arguments
	if (!PyArg_ParseTuple (args, "s#", &buf, &buflen)) {
		return NULL;
	}
	//
	// Retrieve header information
	crs.derptr = (uint8_t *)buf;
	crs.derlen = buflen;
	uint8_t tag;
	size_t len;
	uint8_t hlen;
	if (der_header (&crs, &tag, &len, &hlen)) {
		PyErr_SetFromErrno (PyExc_OSError);
		return NULL;
	}
	//
	// Form a tuple with the values tag, len, hlen
	retval = Py_BuildValue ("(iii)",
			(int) tag,
			(int) len,
			(int) hlen);
	if (retval == NULL) {
		return NULL;
	}
	// "retval" is a new reference
	//
	// Cleanup and return
	return retval;
}


static PyMethodDef der_methods [] = {
	{ "der_unpack", quickder_unpack, METH_VARARGS, "Unpack from DER encoding with Quick DER" },
	{ "der_pack",   quickder_pack,   METH_VARARGS, "Pack into DER encoding with Quick DER" },
	{ "der_header", quickder_header, METH_VARARGS, "Analyse a DER header with Quick DER" },
	{ NULL, NULL, 0, NULL }
};


char module___doc__[] = "Quick `n' Easy DER library";

#if PY_MAJOR_VERSION >= 3
  static struct PyModuleDef moduledef = {
	PyModuleDef_HEAD_INIT,
	"_quickder",		 /* m_name */
	module___doc__,	  /* m_doc */
	-1,				  /* m_size */
	der_methods,		 /* m_methods */
	NULL,				/* m_reload */
	NULL,				/* m_traverse */
	NULL,				/* m_clear */
	NULL,				/* m_free */
  };
#endif


static PyObject *
moduleinit(void)
{
	PyObject *m;

#if PY_MAJOR_VERSION >= 3
	m = PyModule_Create(&moduledef);
#else
	m = Py_InitModule3("_quickder", der_methods, module___doc__);
#endif

	if (m == NULL)
		return NULL;

  return m;
}

#if PY_MAJOR_VERSION < 3
	PyMODINIT_FUNC
	init_quickder(void)
	{
		moduleinit();
	}
#else
	PyMODINIT_FUNC
	PyInit__quickder(void)
	{
		return moduleinit();
	}
#endif
