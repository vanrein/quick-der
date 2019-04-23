// Combine all the .c parts into one file

#include <arpa2/quick-der.h>

/* INLINE FUNCTION #include "der_isconstructed.c" */
/* INLINE FUNCTION #include "der_isprimitive.c"   */
/* INLINE FUNCTION #include "der_isnonempty.c"    */
/* INLINE FUNCTION #include "der_isnull.c"        */
#include "der_header.c"
#include "der_walk.c"
#include "der_skipenter.c"
#include "der_unpack.c"
#include "der_iterate.c"
#include "der_pack.c"
#include "der_prepack.c"
