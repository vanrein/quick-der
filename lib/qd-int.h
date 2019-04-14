/* Internal includes for Quick-DER */


#ifdef DEBUG
#  include <stdio.h>
#  define DPRINTF printf
#else
#  define DPRINTF(...)
#endif


#ifdef DEBUG
#  define DER_DUMP(crs) { FILE *_tmp=popen("derdump /dev/stdin","w"); if(_tmp) { fwrite(crs.derptr,1,crs.derlen,_tmp)); pclose (_tmp); }}
#else
#  define DER_DUMP(crs)
#endif
