/*
 * Test Quick-DER by dumping some LDAP messages.
 *
 * This code is intended to be an exhaustively documented example of the
 * kinds of things you can do with Quick-DER when dealing with binary data.
 */

/* Since we're dealing with LDAP, defined in RFC4211, use that header. */
#include <quick-der/rfc4511.h>
#include <quick-der/api.h>

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <sys/types.h>
#include <sys/stat.h>

const char usage[] = "Usage: ldapsearch.test <filename>\nReads filename and uses Quick-DER to dump the LDAP message inside.\n";

/* Reads a given @p filename and returns a freshly-allocated buffer
 * containing the contents of that file. File must be < 16k in size.
 * The buffer becomes owned by the caller, who should free() it
 * eventually. Returns NULL on any error and prints error reasons
 * to stderr.
 *
 * If @p filesize is non-NULL, it is updated to reflect the size
 * of data read (e.g. the size of the returned buffer), or updated
 * to -1 on any error.
 */
char *load_file(const char *filename, ssize_t *filesize)
{
	if (filesize)
	{
		*filesize = -1;
	}

	int fd;
	if ((fd = open(filename, O_RDONLY)) < 0)
	{
		perror("Input file open():");
		fputs(usage, stderr);
		return NULL;
	}

	struct stat sb;
	if (fstat(fd, &sb) < 0)
	{
		perror("Input file stat():");
		close(fd);
		return NULL;
	}

	if (sb.st_size > 16384)
	{
		close(fd);
		fputs("-- Input file is too large.\n", stderr);
		return NULL;
	}
	if (sb.st_size < 1)
	{
		close(fd);
		fputs("-- Input file is empty.\n", stderr);
		return NULL;
	}

	char *buffer = malloc(sb.st_size);
	if (!buffer)
	{
		perror("Input file malloc():");
		close(fd);
		return NULL;
	}

	ssize_t readsize = read(fd, buffer, sb.st_size);
	if (readsize < 0)
	{
		perror("Input file read():");
		close(fd);
		free(buffer);
		return NULL;
	}
	close(fd);
	if (readsize != sb.st_size)
	{
		free(buffer);
		fputs("-- Input file was not fully read.\n", stderr);
		return NULL;
	}

	if (filesize)
	{
		*filesize = sb.st_size;
	}
	return buffer;
}

int ldapdecode(const char *message, ssize_t message_size)
{
	dercursor crs;
	crs.derptr = message;
	crs.derlen = message_size;

	DER_OVLY_rfc4511_LDAPMessage rq;
	memset(&rq, 0, sizeof(rq));
	dercursor rq_walk[] = { DER_PACK_rfc4511_LDAPMessage };

	int r = der_unpack(&crs, rq_walk, &rq, 1);
	if (r < 0)
	{
		return r;
	}
	if (message_size != ((const char *)crs.derptr - message))
	{
		fprintf(stderr,"! Message was not completely consumed: %d bytes left.", (int) ((const char *)crs.derptr - message));
		return -1;
	}

	fprintf(stdout, ".. Got message ID %p %d\n", (void *)rq.messageID.derptr, (int)rq.messageID.derlen);
	if (!rq.messageID.derptr || (rq.messageID.derlen > 4) || (rq.messageID.derlen < 1))
	{
		fprintf(stderr, "! Unusual message ID length.\n");
		return -1;
	}

	int32_t messageID;
	if (!der_get_int32(rq.messageID, &messageID))
	{
		fprintf(stdout, ".. Get message ID=%d\n", messageID);
	}
	else
	{
		fprintf(stderr, "! Unpacking message ID failed.\n");
		return -1;
	}
	fprintf(stdout, ".. Message cursor %p -> %p, %d bytes used.\n", message, crs.derptr, (int) ((const char *)crs.derptr - message));
	return r;
}

int main(int argc, char **argv)
{
	if (argc != 2)
	{
		fputs(usage, stderr);
		fputs("-- Missing file argument.\n", stderr);
		return 1;
	}

	ssize_t buffer_size = 0;
	char *buffer = load_file(argv[1], &buffer_size);
	if (!buffer)
	{
		/* Error has already been printed */
		return 1;
	}

	fprintf(stderr, "%d\n", ldapdecode(buffer, buffer_size));

	free(buffer);
	return 0;
}
