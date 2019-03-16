

class Tokenizer (object):

	"""Abstract class for JSON tokenization.  Gives an iterator,
	   with additional functions for raising syntax errors that
	   can mention contextual information such as positions, and
	   a facility for looking ahead without consuming a token.

	   Implementations of this class can be had for strings,
	   files and even JSON or Python data structures.

	   Instances of this class, or factually a subclass, can be
	   passed through Quick DER classes while they are being
	   created.  Most code will be generic, but exploit things
	   like variable names and recipes in the concrete subclasses
	   that reflect ASN.1 types.
	"""

	def __init__ (self):
		self.preview = []
		self.eof = False
		self.pos_returned = None

	def syntax_error (self, msg, pos=None, lookahead=0):
		"""Raise a syntax error exception.  Use as much from
		   the context, notably positions, as possible.  This
		   can be provided in part by subclasses.

		   This function only *returns* the error class and
		   has no other impact on the iterator or parsing
		   process, so you hould use it like this:

			raise it.syntax_error ("Out of breath")

		   A position may be supplied to the code; if not,
		   lookahead_tokens indicates any lookahead or 0
		   for the last position returned (1 would already
		   be lookahead).
		"""
		if pos is None:
			if lookahead >= len (self.preview):
				(pos,_tok) = self.preview [lookahead]
			else:
				pos = self.pos_returned
		pos_str = self.position_string (pos)
		return Exception ("Syntax error at %s: %s" % (pos_str,msg))

	def lookahead (self, lookahead=1):
		"""Look ahead to an upcoming token.  The normal
		   look-ahead is 1 token after the current, but
		   more is possible.  Looking ahead will not
		   change the iterator progression.  Looking back
		   is not possible.

		   This function may raise syntax errors by
		   calling the superclass and raising the result.
		"""
		while lookahead > len (self.preview):
			next_one = self.parse_next ()
			if next_one [1] is None:
				self.eof = True
				return next_one
			self.preview.append (next_one)
		(self.pos_returned,retval) = self.preview [skip_tokens-1]
		return retval

	def parse_next (self):
		"""The parse_next() method yields the next (pos,token).
		   The token is the part of the text that represents
		   the next parser input token, or None when no more
		   tokens are available.  The pos is the position of
		   the token in a format yet to be tranformed with
		   position_string() before printing it.

		   Implementations should attempt to return a slice
		   of a larger structure, so as to preserve memory.

		   The iterator class might return it directly, or
		   a lookahead attempt may store it in the preview
		   list.
		"""
		raise NotImplemented ("Subclasses should override this function")

	def position_string (self, pos):
		"""Positions as returned by parse_next() are considered
		   abstract until they are needed for error printing.
		   At this time, position_string() is called to map
		   the position into a readable form.  It may be an
		   integer line number, or a (line,column) or similar.

		   The split minimises the burden on memory for parser
		   positions.  This works in tandem with string slicing,
		   which also helps to make the parser efficient.
		"""
		raise NotImplemented ("Suclasses should override this function")

	def __iter__ (self):
		"""Iterator implementation method."""
		return self

	def next (self):
		"""Iterator implementation method."""
		if len (self.preview) > 0:
			(self.pos_returned,retval) = self.preview.pop (0)
			return retval
		else:
			(self.pos_returned,retval) = self.parse_next ()
			if retval is None:
				self.eof = True
				raise StopIteration ()
			return retval


class StringTokenizer (Tokenizer):

	import re

	rex_ws = '[ \r\t\n]*'

	rex_strchr = '[\[\{\}\]:,]'
	rex_value  = '(?:true|false|null)'  #TODO# word boundaries required by JSON?
	rex_string = '(?:"[^"]*")'
	rex_number = '(?:-?(?:0|[1-9][0-9]*)(?:[.][0-9]+)?(?:[eE][0+]?[0-9]+)?)'

	re_token = re.compile ('(%s|%s|%s|%s)' % (rex_strchr,rex_value,rex_string,rex_number) )

	"""JSON tokenizer for a string.
	"""

	def __init__ (self, jsonstr):
		Tokenizer.__init__ (self)
		self.jsonstr = jsonstr
		self.pos = 0

	def position_string (self, pos):
		"""The abstract position is simply the index into the
		   string.  We will use it to count line numbers and
		   return a line,column format string for use in
		   error messages.
		"""
		line =   1 + self.jsonstr [:self.pos].count ('\n')
		col  = pos - self.jsonstr.rfind ('\n', 0, pos)
		return '%d,%d' % (line,col)

	def parse_next (self):
		while self.pos < len (self.jsonstr):
			if self.jsonstr [self.pos] not in ' \t\r\n':
				break
			self.pos += 1
		if self.pos == len (self.jsonstr):
			# Signel end of file
			return (self.pos,None)
		cur = self.re_token.match (self.jsonstr, self.pos)
		if cur is None:
			raise self.syntax_error ('Unknown symbol', pos=self.pos)
		token = cur.group ()
		retval = ( self.pos, token )
		self.pos += len (token)
		return retval

