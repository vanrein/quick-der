/*
 * This file is part of Quick DER, version 1.2.
 *     https://github.com/vanrein/quick-der
 *
 * Copyright (c) 2016-2017 Rick van Rein, OpenFortress.nl
 * Copyright (c) 2017, Adriaan de Groot <groot@kde.org>
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without modification,
 * are permitted provided that the following conditions are met:
 *
 *   1. Redistributions of source code must retain the above copyright notice,
 *      this list of conditions and the following disclaimer.
 *
 *   2. Redistributions in binary form must reproduce the above copyright notice,
 *      this list of conditions and the following disclaimer in the documentation
 *      and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
 * IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
 * OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef QUICK_DER_H
#define QUICK_DER_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <errno.h>


#ifdef DEBUG
#  include <stdio.h>
#  define DPRINTF printf
#else
#  define DPRINTF(...)
#endif


#ifndef EBADMSG
#  define EBADMSG EBADF
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* Most of BER is included with these routines as well, but not the
 * indefinate-length method.  Also, there is no support for application,
 * contextual and private tags [31] and up.  What this means in practice,
 * is that you should be able to process PKIX certificates, in spite of
 * their outer layer being BER and only the tbsCertificate being DER.
 */


/* Cursors describe the ASN.1 buffer in DER coding, and can be walked into
 * structures when they follow a path.  It is possible to make copies of this
 * structure between partial traversals, so as to efficiently run into a
 * structure.
 */
typedef struct dercursor {
	uint8_t *derptr;
	size_t   derlen;
} dercursor;


/* Unpacked DER structures take the same shape as a dercursor, and usually
 * overlay the same space; it is assumed that the programmer is aware of
 * the phase his program is in, and addresses the right variation.  Most
 * often, this type will not be used, but a properly typed structure with
 * the same names.  The derray points to an array of dercursors, which is
 * then overlayed with a structure with dercursors named after fields in
 * the ASN.1 syntax; the dercnt value indicates how many elements dercursors
 * exist in the DER data.
 *
 * This variation is useful for dynamically-sized data, notably from unpacking
 * SEQUENCE OF and SET OF substructures.
 */

typedef struct derarray {
	union dernode *derray;
	size_t dercnt;
} derarray;


/* Prepacked DER structures finally, also overlay the dercursor and/or the
 * derarray structures, to cover yet another phase of the process.  In this
 * case, there still is a pointer to a derarray, but it has been marked with
 * a variation on the length, namely with the most significant bit set.  This
 * makes the variation recognisable during the packing process, without
 * really affecting the potential of an in-memory stored data structure.
 */

#define DER_DERLEN_FLAG_CONSTRUCTED ((~(size_t)0)^((~(size_t)0)>>1))
#define DER_DERLEN_ERROR ((~(size_t)0)>>1)

typedef struct derprep {
	dercursor *derray;
	size_t derlen_msb;
} derprep;


/* The above structures may be overlaid in a union, but since the derray is
 * usually replaced with another component, a variation is used by generated
 * code.  Especially the "info" variation is then usually replaced by an
 * overlay structure with names taken from the ASN.1 syntax.  For home-brewn
 * parsers however, we do include a generic union below.
 *
 * The variation "wire" refers to the format on the wire, so plain DER.
 * The variation "info" refers to an unpacked array of dercursors.
 * The variation "prep" refers to a form that is prepared for sending.
 */
typedef union dernode {
	dercursor wire;
	derarray info;
	derarray prep;
} dernode;


/* WRITING GOOD DER TARVERSAL PATHS.
 *
 * A path constitutes a “lazy” parser going through a DER structure.  It will
 * trigger faults when it runs into them, but will otherwise be quite permissive.
 * The lazy thing is that it simply advances a cursor to move through the ASN.1
 * specification.
 *
 * To write an ASN.1 path expression, know the place where your cursor starts,
 * which usually is the entire structure you stored in a buffer, and know where
 * it should end.  To get to the end point, you will need to do a series of
 * actions, namely skipping entries and entering other entries.  A path is
 * basically a series of such steps.
 *
 * The ASN.1 syntax assures parseability with only one tag of lookahead.  This
 * means that at any choice point in the syntax, you can safely skip ahead to the
 * one you meant to find.  So, ignore a CHOICE and skip any OPTIONAL bits
 * unless they are actually part of your path.
 *
 * The path traversal mechanism is a lazy syntax check, meaning it will check
 * precisely those parts that it needs to traverse the path, but accept anything
 * else without giving it a second look.  In other words, the code is sufficiently
 * secure to not accept badly formatted data, but only inasfar as you actually
 * need that data.  To this end, an OPTIONAL tag may be skipped by prefixing
 * it with a special tag, and a CHOICE may be skipped regardless of the actual
 * choice it made (if you want to enter either form, you should simply indicate
 * the desired tag and the parser may return that it stopped being able to parse
 * the structure from that point in your code, which tells you to try another path
 * from the cursor position).  And yes, you can have an optional choice by
 * first using DER_WALK_OPTIONAL, DER_WALK_CHOICE, DER_TAG_…
 *
 * Path components are specified by their tags, for which definitions follow; in
 * addition, a flag DER_WALK_SKIP or DER_WALK_ENTER
 * should be added to signal skip or enter.  Note that the
 * first component is not being matched; you should compare its tag by
 * looking what the cursor points at.  You should first ensure that you did not
 * end up in an empty data structure though.  Paths are stored in derwalk[]
 * that end in DER_WALK_END.
 *
 * There is no support for the long-form tag; that is, tags 31 with continued
 * tag bytes; it is assumed that a tag always fits in one byte and otherwise
 * ENOTIMPL is reported.
 *
 * An example path, with made-up ASN.1 markup in comments, is:
 *
 *	derwalk [] = {
 *		DER_WALK_ENTER | DER_TAG_SEQUENCE,      // SEQUENCE OF
 *		DER_WALK_ENTER | DER_TAG_CONTEXT (0),   // [0]
 *		DER_WALK_OPTIONAL,
 *		DER_WALK_SKIP  | DER_TAG_BOOLEAN,       // amActive BOOLEAN OPTIONAL
 *		DER_WALK_CHOICE   ,                     // myMood CHOICE { …. }
 *		DER_WALK_SKIP  | DER_TAG_OCTET_STRING,  // myNAME OCTET STRING
 *		DER_WALK_ENTER | DER_TAG_SEQUENCE,      // options SEQUENCE OF
 *		DER_WALK_END
 *	};
 *
 * Having found the sequence we’re interested in, we could iterate over its
 * elements.
 *
 * There certainly is room for a developer’s tool that creates such paths from a
 * textual description and the ASN.1 syntax description.  Perhaps the formats
 * used by libtasn1 could help doing this.  Compared to libtasn1, the advantage
 * of this approach is that the code is simpler, memory management is simplified
 * by using shared data, and that ought to improve efficiency rather dramatically.
 */

typedef uint8_t derwalk;

/* Special markers for instructions on a walking path */
#define DER_WALK_END 0x00
#define DER_WALK_OPTIONAL 0x3f
#define DER_WALK_CHOICE 0x1f
#define DER_WALK_ANY 0x1f

/* Special markers for instructions for (un)packing syntax */
#define DER_PACK_LEAVE 0x00
#define DER_PACK_END 0x00
#define DER_PACK_OPTIONAL 0x3f
#define DER_PACK_CHOICE_BEGIN 0x1f
#define DER_PACK_CHOICE_END 0x1f
#define DER_PACK_ANY 0xdf

/* Flags to add to tags to indicate entering or skipping them */
#define DER_WALK_ENTER 0x20
#define DER_WALK_SKIP  0x00
#define DER_WALK_MATCHBITS (~(DER_WALK_ENTER | DER_WALK_SKIP))

/* Flags to add to tags to indicate entering or storing them while (un)packing */
#define DER_PACK_ENTER 0x20
#define DER_PACK_STORE 0x00
#define DER_PACK_MATCHBITS (~(DER_PACK_ENTER | DER_PACK_STORE))

/* Universal tags and macros for application, contextual, private tags */
#define DER_TAG_BOOLEAN 0x01
#define DER_TAG_INTEGER 0x02
#define DER_TAG_BITSTRING 0x03
#define DER_TAG_BIT_STRING 0x03
#define DER_TAG_OCTETSTRING 0x04
#define DER_TAG_OCTET_STRING 0x04
#define DER_TAG_NULL 0x05
#define DER_TAG_OBJECTIDENTIFIER 0x06
#define DER_TAG_OBJECT_IDENTIFIER 0x06
#define DER_TAG_OID 0x06
#define DER_TAG_OBJECT_DESCRIPTOR 0x07
#define DER_TAG_EXTERNAL 0x08
#define DER_TAG_REAL 0x09
#define DER_TAG_ENUMERATED 0x0a
#define DER_TAG_EMBEDDEDPDV 0x0b
#define DER_TAG_EMBEDDED_PDV 0x0b
#define DER_TAG_UTF8STRING 0x0c
#define DER_TAG_RELATIVEOID 0x0d
#define DER_TAG_RELATIVE_OID 0x0d
#define DER_TAG_SEQUENCE 0x10
#define DER_TAG_SEQUENCEOF 0x10
#define DER_TAG_SEQUENCE_OF 0x10
#define DER_TAG_SET 0x11
#define DER_TAG_SETOF 0x11
#define DER_TAG_SET_OF 0x11
#define DER_TAG_NUMERICSTRING 0x12
#define DER_TAG_PRINTABLESTRING 0x13
#define DER_TAG_T61STRING 0x14
#define DER_TAG_TELETEXSTRING 0x14
#define DER_TAG_VIDEOTEXSTRING 0x15
#define DER_TAG_IA5STRING 0x16
#define DER_TAG_UTCTIME 0x17
#define DER_TAG_GENERALIZEDTIME 0x18
#define DER_TAG_GRAPHICSTRING 0x19
#define DER_TAG_VISIBLESTRING 0x1a
#define DER_TAG_GENERALSTRING 0x1b
#define DER_TAG_UNIVERSALSTRING 0x1c
#define DER_TAG_CHARACTERSTRING 0x1d
#define DER_TAG_CHARACTER_STRING 0x1d
#define DER_TAG_BMPSTRING 0x1e

#define DER_TAG_APPLICATION(n) (0x40 | (n))
#define DER_TAG_CONTEXT(n) (0x80 | (n))
#define DER_TAG_PRIVATE(n) (0xc0 | (n))


/* DEFINITION GENERATOR MACROS
 *
 * These macros instantiate the various definitions in the header file
 * under a standard name.  Use DECLARE in header files and forward defs,
 * and use DEFINE to instantiate a mod.tp to a definition.
 */
#define DER_PIMP_DECLARE(mod,tp) extern const derwalk DER_PIMP_##mod##_##tp [];
#define DER_PACK_DECLARE(mod,tp) extern const derwalk DER_PACK_##mod##_##tp [];
#define DER_PSUB_DECLARE(mod,tp) extern const struct psub_somestruct DER_PSUB_##mod##_##tp [];

#define DER_PIMP_DEFINE(mod,tp) const derwalk DER_PIMP_##mod##_##tp [] = { \
	DER_PIMP_##mod##_##tp, \
	DER_PACK_END };
#define DER_PACK_DEFINE(mod,tp) const derwalk DER_PACK_##mod##_##tp [] = { \
	DER_PACK_##mod##_##tp, \
	DER_PACK_END };
#define DER_PSUB_DEFINE(mod,tp) DEFINE_DER_PSUB_##mod##_##tp


/* SUB-PARSER STRUCTURAL SUPPORT
 *
 * The DER_PSUB_ definitions declare lists that can be traversed by a
 * memory-aware application, if it wants to overcome the limitation of
 * Quick DER to not parse SEQUENCE OF and SET OF, which it skips so it
 * can stay small and simple, due to no memory management at all.
 *
 * Each of these structures contain an offset for the repeating type,
 * the size of each of its elements, and then the DER_PACK_ and
 * DER_PSUB_ definitions accommodating its processing.  The final
 * entry is set to { 0, 0, NULL, NULL }.
 */
typedef size_t der_subp_size_t;

typedef struct der_subparser_action {
	der_subp_size_t idx;
	der_subp_size_t esz;
	derwalk *pck;
	struct der_subparser_action *psub;
} der_subparser_action;

#define DER_OFFSET(mod,tp,fld) (offsetof(DER_OVLY_##mod##_##tp,    fld) / sizeof(dercursor))
#define DER_ELEMSZ(mod,tp,fld) (sizeof  (DER_OVLY_##mod##_##tp##_##fld) / sizeof(dercursor))


/* PARSING AN ENTIRE STRUCTURE
 *
 * Although it is useful to be able to construct paths that walk through
 * DER-encoded ASN.1 data, it is often more useful to parse a structure
 * and put its values into a general data structure.  This can be done
 * by describing the entire syntax, in much the same fashion as a walking
 * path that meanders through the entire structure.  Ideally of course,
 * this is automatically derived from an ASN.1 syntax description.
 *
 * The idea of parsing an entire structure is like a depth-first walk
 * through the entire structure, and store all the individual components
 * into a cursor of their own.  The combined cursors can be overlayed
 * by a structure type that has field names to match the ASN.1 syntax,
 * so as to simplify locating entries to use in a program.
 *
 * Where we used symbols starting with DER_WALK_ to describe walking paths,
 * we will use symbols starting with DER_PACK_ to describe the syntax
 * descriptions, and we will use them both for packing and unpacking
 * DER syntax.
 *
 * The flags DER_PACK_ENTER and DER_PACK_STORE indicate what to do with
 * the current item being walked past; _ENTER unfolds a structures and
 * dives into it, with the intention of backing out later using a
 * DER_PACK_LEAVE.  It is normal for the first instruction to have a
 * DER_PACK_ENTER flag.  The alternative flag is DER_PACK_STORE, which
 * indicates that the present tag should not be processed, but instead
 * be stored as a dercursor in the provided output array.
 *
 * Entries immediately following DER_PACK_OPTIONAL (including those
 * structures marked in ASN.1 with a DEFAULT value, which by the way is
 * not installed while unpacking a DER structure) will be skipped when
 * they do not match; in case of DER_PACK_STORE flags, the respective
 * dercursor structures will be set to derptr NULL and derlen 0.
 *
 * The ASN.1 pattern of a CHOICE between alternative substructures is
 * marked between DER_PACK_CHOICE_BEGIN and DER_PACK_CHOICE_END, and may
 * be surrounded by DER_PACK_OPTIONAL_ markers.  Each of the possible
 * substructures is tried on the upcoming DER element, and all that do
 * not match fill a dercursor structure with derptr NULL and derlen 0.
 * As soon as one has matched, it is handled as specified and the
 * remaining choice options are all set to derptr NULL and derlen 0.
 * When encountering DER_PACK_CHOICE_END, it is tested whether one of
 * the choices was fulfilled, except when DER_PACK_OPTIONAL_ markers
 * surround the choice section.
 *
 * Not all elements have a predictable number of dercursors, in which
 * case they must be parses them in a special manner.  This is true
 * for the SEQUENCE OF and SET OF constructs; their total content needs
 * to be _STOREd in a first pass, and separately parsed into an array
 * of dercursors (or an overlayed structure type).  The caller allocates
 * the space where it wants --on the stack or form a heap-- and also
 * has the option of running through the contents with iterators based
 * in the cursor that was _STOREd.
 *
 * Having done all this, we now have a structure that holds the various
 * pieces of our DER structure, with field names that derive from the
 * ASN.1 syntax.  In fact, using the same structural descriptions that
 * also derive from the ASN syntax, we should be able to reproduce the
 * DER information from the parser output structures.
 * (NOTE: Variations in Primitive-or-Constructed?
 */


/* Test if the cursor points to a Constructed type.  Return 1 for yes, 0 for no.
 * Note that too-short structures return 0, so this is not quite the inverse
 * of der_isptimitive().
 */
static inline int der_isconstructed (const dercursor *crs) {
	return (crs->derlen >= 2)? (((*crs->derptr) >> 5) & 0x01): 0;
}

/* Test if the cursor points to a Primitive type.  Return 1 for yes, 0 for no.
 * Note that too-short structures return 0, so this is not quite the inverse
 * of der_isconstructed().
 */
static inline int der_isprimitive (const dercursor *crs) {
	return (crs->derlen >= 2)? (((~ *crs->derptr) >> 5) & 0x01) : 0;
}


/* Ensure that the length available to the cursor is non-empty.  This is sort of
 * a DER-equivalent to a NULL pointer; it normally occurs only during
 * iteration, where it can be used to test whether more data is available.
 * Note that this does not actually read the DER-data, but instead the cursor.
 * This functions return 1 for non-empty, or 0 for empty cursor lengths.
 */
static inline int der_isnonempty (const dercursor *crs) {
	return (crs->derlen == 0)? 0: 1;
}


/* Test whether a cursor is set to a NULL value; this is the case when the
 * data pointed to is actually NULL.
 */
static inline int der_isnull (const dercursor *crs) {
	return (crs->derptr == NULL);
}


/* Analyse the header of a DER structure.  Pass back its tag, len and the
 * total header length.  Analysis starts at crs, which will move past the
 * header by updating both its derptr and derlen components.  This function
 * returns 0 on success, or -1 on error (in which case it sets errno).
 *
 * For BIT STRINGS, this routine validates that remainder bits are cleared.
 * Note that this is a difference between BER and DER; DER requires that
 * the bits are 0 whereas BER welcomes arbitrary values.  In the interest
 * of security (bit buffer overflows) and reproducability of signatures on
 * data, this routine rejects non-zero remainder bits with an error.  For
 * your program, this may mean that the number of remainder bits do not
 * need to be checked if zero bits are acceptable without overflow risk.
 */
int der_header (dercursor *crs, uint8_t *tagp, size_t *lenp, uint8_t *hlenp);


/* Update a cursor expression by walking into a DER-encoded ASN.1 structure.
 * The return value is -1 on error, and errno will be set accordinly, and the
 * cursor will not have been updated.  Otherwise, the return value is the number
 * of unprocessed bytes on the path, so 0 when the entire path was processed.
 * The count as non-error returns, so the cursor is updated.  Values higher than
 * 0 indicate where in the path a tag could not be found; this may be helpful in
 * learning about the structure that was being parsed, for example that an
 * OPTIONAL or CHOICE part was absent from the DER bytes.
 *
 * Paths are sequence of one-byte choices to be made.  These choices are tags,
 * because these are used by ASN.1 to decide on parsing choices to be made.
 * The one difference is the interpretation of the Primitive/Constructed bit: when
 * this is set to Primitive, the value will be skipped (even if it is Constructed)
 * and when set to Constructed, the value will be entered and interpreted as ASN.1
 * (even when it is setup as Primitive).
 *
 * In all the places where ASN.1 defines choices, such as CHOICE or OPTIONAL,
 * it enforces distinct tags from the various choices.  This can be used in a path
 * to skip such unknown parts in the encoding.
 *
 * When entering a BIT STRING, special treatment is implemented; the remaining
 * bits will have to be zero, and these are then skipped while entering the
 * remainder.  Note that this ensures that the byte-aligned DER structures are
 * properly packed into a bit-aligned BIT STRING container.
 */
int der_walk (dercursor *crs, const derwalk *path);


/* Skip the current value under the cursor.  Return an empty cursor value
 * if nothing more is to be had.
 * This function returns -1 on error and sets errno; 0 on success.
 */
int der_skip (dercursor *crs);


/* Enter the current value under the cursor.  Return an empty cursor value
 * if nothing more is to be had.  Some special handling is done for BIT STRING
 * entrance; for them, the number of remainder bits is required to be 0 and
 * that initial byte is skipped.
 *
 * This function returns -1 on error and sets errno; 0 on success.
 */
int der_enter (dercursor *crs);


/* Assuming that we are looking at a concatenation of DER elements, focus on
 * the first one.  That is, chop off anything beyond the first element.
 *
 * This function returns -1 on error and sets errno; 0 on success.
 */
int der_focus (dercursor *crs);


/* Unpack a structure, or possibly a sequence of structures.  The output
 * is stored in subsequent entries of outarray, whose size should be
 * precomputed to sufficient length.  The outarray will often be an
 * overlay for a structure composed of dercursor elements with labels
 * and nesting derived from ASN.1 syntax, and matching an (un)packing walk.
 *
 * The syntax is supplied without a length; proper formatting of the syntax
 * is assumed, that is the number of DER_PACK_ENTER bits should be followed
 * by an equal amount of DER_PACK_LEAVE instructions, and the choice
 * markers DER_PACK_CHOICE_BEGIN ... DER_PACK_CHOICE_END must be properly
 * nested with those instructions and with each other.  There is no
 * protection for foolish specifications (and they will often be generated
 * anyway).  This method additionally requires the first element in the
 * syntax to be flagged with DER_PACK_ENTER.  (TODO: Permit non-looped use?)
 *
 * The cursor will be updated by this call to point to the position
 * where unpacking stopped.  Refer to the return value to see if this is
 * an error position.  The function returns 0 on success and -1 on failure.
 * Upon failure, errno is also set, namely to EBADMSG for syntax problems
 * or ERANGE for lengths or tags that are out of the supported range of
 * this implementation.
 */
int der_unpack (const dercursor *crs, const derwalk *syntax,
			dercursor *outarray, int repeats);


/* Given a dercursor, setup an iterator to run over its contained components.
 * While iterating, the initial iterator must continue to be supplied, without
 * modification to it.
 *
 * NOTE THE DIFFERENT CALLING CONVENTION FOR THIS FUNCTION!
 *
 * This function returns 1 upon success.  In case of failure such as no
 * elements found, it returns 0.
 *
 * To be sensitive to empty lists, use this as follows:
 *
 *	if (der_iterate_first (cnt, &iter)) do {
 *		...process entry...
 *	} while (der_iterate_next (&iter));
 *
 */
int der_iterate_first (const dercursor *container, dercursor *iterator);

/* Step forward with an iterator.  This assumes an iterator that was
 * setup by der_iterate_first() and has since then not been modified.
 *
 * NOTE THE DIFFERENT CALLING CONVENTION FOR THIS FUNCTION!
 *
 * This function returns 1 upon success.  In case of failure, it
 * returns 0; in addition, it sets the nested iterator for zero
 * iterations.  A special case of error is when the container cursor is
 * not pointing to a Constructed element; in this case an error is returned
 * but the cursor will run over the contained elements when using the iterator.
 *
 * To be sensitive to errors, use this as follows:
 *
 *	if (der_iterate_first (cnt, &iter)) do {
 *		...process entry...
 *	} while (der_iterate_next (&iter));
 *
 */
int der_iterate_next (dercursor *iterator);


/* Count the number of elements available after entering the component
 * under the cursor.  This is useful to know how many elements exist inside
 * a SEQUENCE OF or SET OF, but may be used for other purposes as well.
 */
int der_countelements (dercursor *container);


/* COMPOSING DER STRUCTURES FOR TRANSMISSION
 *
 * While working with DER data, the various dercursor structures can be passed
 * around freely, because they are mere <pointer,length> tuples that reference
 * independently management memory -- usually an input buffer.  As long as the
 * input buffer is not cleared, the tuples can be carried around and copied
 * and destroyed at will.
 *
 * Just like overlay structures are filled with dercursor fields labelled
 * according to the ASN.1 syntax during der_unpack(), it is also possible to
 * build up such structures for output with der_pack().  These structures
 * must once more refer to independently allocated memory, which may be any
 * mixture of sources: input buffers, stack portions, heap structures.  As
 * long as these memory regions are kept around during der_pack().  After
 * der_pack(), a new output area has been filled and the fragments can be
 * cleared, deallocated and so on.
 *
 * The der_pack() routine is based on the same DER_PACK_ syntax descriptions
 * used by der_unpack(), so it is straightforward to unpack a structure, make
 * some modifications and pack its new incarnation.
 *
 * One point of concern is the DER_STORE_ structure.  This can both be used
 * for Primitive types and for Constructed types such as SEQUENCE OF and
 * SET OF that either need an additional call to der_unpack() to be parsed,
 * or iteration, or der_walk().  Reproducing those pieces literally is not
 * a problem, and leads to the original data as a Primitive type.  But when
 * the data is in fact Constructed, or perhaps modified, something else is
 * required.  To accommodate that, you may need to der_prepack() such partial
 * structures that are to be dealt with a Constructed types; most commonly
 * however, is that this is necessary for SEQUENCE OF and SET OF, which never
 * occur as Primitive types, and are therefore always treated correctly.
 *
 * The general idea of der_prepack() is that you supply a dercursor array
 * and set it up in the original structure stored by DER_STORE_.  This
 * leads to a different representation that will be recognised by
 * der_pack() as a reference to such an array, which it will insert as
 * a Constructed subtype, with the tag that it originally had during
 * parsing.  Specifically, the highest bit of derlen, identified by the
 * symbol DER_DERLEN_FLAG_CONSTRUCTED, will be set to indicate that the
 * remainder of the derlen is to be interpreted as a number of dercursors,
 * to be found at the derptr.  This differs from the usual meaning, which
 * is a literal series of bytes pointed to by derptr and whose length is
 * stored in derlen.  TODO: Do we really want to do it this way?!?
 *
 * Note that the special ASN.1 constructs "ANY" and "ANY DEFINED BY" are
 * not a problem.  They are stored with the tag and length included, and
 * are therefore trivial to reproduce.  Also, the CHOICE and OPTIONAL
 * versions are trivially handled by having NULL dercursors.  Do avoid
 * calling der_pack() with multiple options in one CHOICE set though.
 *
 * Based on all this, the der_pack() routine can scan over the syntax,
 * look at the data at hand and determine what needs to go where.  It
 * is often good to know the storage space before writing, and
 * der_packlen() can be used to determine that.
 *
 * Since der_pack() assumes it is provided with the properly sized
 * memory buffer to write to, it will start at the end and work its
 * way back.  This means that lengths are known at their time of
 * insertion into the buffer.  The idea stems from MIT Kerberos5,
 * but unlike that implementation we do use a "forward" description
 * and merely traverse it from the end to the beginning.  Note that
 * the DER_PACK_ descriptions lend themselves well for doing this.
 */


/* Pack a memory buffer following the indicated syntax, and using the elements
 * stored in the derray.  Enough memory is assumed to be available _before_
 * outbuf_end_opt; to find how large this buffer needs to be, it is possible to
 * call this function with outbuf_end_opt set to NULL.
 *
 * The return value is the same, regardless of outbuf_end_opt being NULL or not;
 * it is the length of the required output buffer.  When an error occurs, the
 * value 0 is returned, but that cannot happen on a second run on the same data
 * with only the outbuf_end_opt set to non-NULL.
 *
 * Please note once more that outbuf_end_opt, when non-NULL, points to the
 * first byte that is _not_ filled with the output DER data.  The value will
 * be decremented in this function for the bytes written.  This is quite
 * simply a more optimal strategy for DER production than anything else.
 * And yes, this is funny in an API, but you have the information and we would
 * otherwise ask you to pass it in, need to check it, you would then need to
 * check for extra error returns, ... so this is in fact simpler.
 *
 * Any parts of this structure that need to be prepacked are assumed to have
 * been prepared with der_prepack().  If your packaged structures show up as
 * Primitive where they should have been Constructed, then this is where to
 * look.
 */
size_t der_pack (const derwalk *syntax, const dercursor *derray,
					uint8_t *outbuf_end_opt);


/* Pre-package the given DER array into the dercursor that is also provided.
 * This operation modifies the information stored in the destination field,
 * in a way that stops it from being interpreted properly in the usualy
 * manner, but it _does_ prepare it for der_pack() in a way that will include
 * the array of dercursor as a consecutive sequence, without any additional
 * headers, markers or other frills.
 */
void der_prepack (dercursor *derray, size_t arraycount, derarray *target);



/* PACKING AND UNPACKING DATA
 *
 * A cursor points to a particular sequence of bytes, but those data-bytes
 * are still encoded. The convenience functions for packing and unpacking
 * turn those data bytes into regular C types (or vice-versa).
 */

/* Unpack a single integer. The integer value is stored in *valp, while
 * success is indicated through the return value: 0 for success, -1 if
 * the value cannot be represented in a 32-bit integer.
 *
 * On failure, the value stored in *valp is unchanged.
 *
 * It is legal to pass a NULL valp, in which case the return value tells
 * you if the integer could be represented (or not). The DER cursor must
 * be valid and point to valid memory.
 */
int der_get_int32 (dercursor cursor, int32_t *valp);

/* Unpack a single unsigned integer. See also der_get_int32(). */
int der_get_uint32 (dercursor cursor, uint32_t *valp);

/* Pack an Int32 or UInt32 and return the number of bytes.
 *
 * The buffer types der_buf_int32_t and der_buf_uint32_t can hold the size of
 * the longest possible value, excluding header.  The return value from the
 * function indicates the actual number of bytes used.  The buffer pointer
 * and return value can be combined to hold another dercursor.
 *
 * These functions never fail.  Note that a returned derlen of 0 is valid.
 *
 * For the curious: the reason that der_buf_uint32_t is 5 bytes while
 * der_buf_int32_t is only 4 bytes is that DER represents the INTEGER
 * type in 2's complement, using the most compact representation possible.
 * Unsigned values >= 0x80000000 need an extra byte 0x00 prefixed to avoid
 * being interpreted as negative values.
 */
typedef uint8_t der_buf_int32_t [4];
dercursor der_put_int32 (uint8_t *der_buf_int32, int32_t value);
typedef uint8_t der_buf_uint32_t [5];
dercursor der_put_uint32 (uint8_t *der_buf_uint32, uint32_t value);

/* 
 * Unpack a BOOLEAN and set its value to 0 for FALSE, or 1 for TRUE.
 *
 * Do accept all BER encodings of BOOLEAN, meaning, any non-zero byte is
 * interpreted as TRUE, even though DER is more explicit with 0xff.
 *
 * Upon encountering an error, return -1; success decoding as BER is 0.
 * Even when an error is reported, the value is updated, so it is safe
 * to ignore the error in order to facilitate a more lenient parser
 * even than BER.  Even when excessive in size, the value is set to
 * FALSE only when all bytes (possibly zero bytes) are 0x00.
 */
bool der_get_bool (dercursor crs, int *valp);
/* 
 * Pack a BOOLEAN and return the number of bytes.  Do not pack a header
 * around it.  The function always packs to one byte, and encodes
 * TRUE as 0xff and FALSE as 0x00, as required by DER.  It interprets
 * the provided boolean value as TRUE when it is non-zero, as common
 * in C.
 *
 * Use the der_buf_bool_t as a pre-sized buffer for the encoded value.
 * This function always returns successfully.
 */
typedef uint8_t der_buf_bool_t [1];
dercursor der_put_bool (uint8_t *der_buf_bool, bool value);

/* Compare the values pointed to by cursors @p c1 and @p c2.
 * Returns 0 if the (binary) values are equal, otherwise returns
 * the difference between the first two differing bytes (similar
 * to memcmp(3) with different parameters). Zero length data is
 * considered equal. If the value in @p c1 is a prefix of the
 * data in @p c2, returns -1 (less than).
 *
 * Does not know about semantics: a FALSE (DEFAULT) boolean is
 * still different from a FALSE boolean, since the former has
 * zero length, while the latter has non-zero length, with a zero value.
 */
int der_cmp(dercursor c1, dercursor c2);

#ifdef __cplusplus
}
#endif

#endif /* QUICK_DER_H */
