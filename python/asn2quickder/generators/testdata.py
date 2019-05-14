from asn1ate.sema import DefinedType, SimpleType, BitStringType, ValueListType, NamedType, TaggedType, ChoiceType, \
    SequenceType, SetType, SequenceOfType, SetOfType, dependency_sort, TypeAssignment, TagImplicitness, ExtensionMarker, \
    ComponentType

from asn2quickder import packstx as api
from asn2quickder.generators import QuickDERgeneric


class QuickDER2testdata(QuickDERgeneric):
    """This builds a network of generators that exhibits the structure
       of the data, generating test variations for each of the parts.
       For each named type, an entry point for the network is setup in
       a dictionary, from which any number of test cases can be retrieved.

       The search structure for the generators is width-first, meaning
       that structures first seek out variations at the outer levels,
       using already-found cases for end points, and only later start
       to vary deeper down.  This way, test cases can be enumerated
       in a consistent manner and tests become reproducable, even when
       the total work load for testing is rediculously high.  The
       width-first approach was chosen because often a type includes
       other named types, which may be tested independently.

       The deliverable of the type-processing routines is a tuple
       (casecount,casegenerator) where the casecount gives the total
       number of tests available (usually much larger than deemed
       interesting for a test) and where the casegenerator can be
       asked to generate one numbered test case.  This allows us to
       both generate "the first 100 tests" and any specific test or
       range of tests that we might be interested in (perhaps we
       got an error report on case 1234567 and would like to make
       it a standard test).

       The reason we speak of a network of generators is that the
       various definitions are connected, often in a cyclical
       manner, and to that end they lookup values in the dictionary
       that maps type names to (casecount,casegenerator) tuples.
       These are not generators in the Python3 sense however, as
       these would not allow us to request arbitrary entries such
       as the aforementioned test case 1234567.  It is closer to
       a functional programming concept with closures standing by
       to operate on a given index in a (virtual) output list.

       The efficiency might be poor if we generated each case for
       each type name freshly, because there will be a lot of
       repeated uses.  To make the case generators operate more
       smoothly, they may employ a cache, perhaps based on weak
       references.

       This class can hold the network of generators as well as
       their cache structures, and supports output of test data
       in individual files.  As an alternative use case, one may
       consider delivering test cases over a stream, such as an
       HTTP API.
    """

    def __init__(self, semamod, outfn, refmods):
        self.semamod = semamod
        self.refmods = refmods
        # Open the output file
        super(QuickDER2testdata, self).__init__(outfn, '.testdata')
        # Setup the function maps for generating Python
        self.type2tdgen = {}
        self.funmap_tdgen = {
            DefinedType: self.tdgenDefinedType,
            SimpleType: self.tdgenSimple,
            BitStringType: self.tdgenSimple,
            ValueListType: self.tdgenSimple,
            NamedType: self.tdgenNamedType,
            TaggedType: self.tdgenTagged,
            ChoiceType: self.tdgenChoice,
            SequenceType: self.tdgenConstructed,
            SetType: self.tdgenConstructed,
            SequenceOfType: self.tdgenRepeated,
            SetOfType: self.tdgenRepeated,
        }

    def fetch_one(self, typename, casenr):
        # TODO# Check in weakref cache if already generated
        (max_, fun) = self.type2tdgen[typename]
        if casenr >= max_:
            return None
        assert casenr < max_, 'Case number out of range for ' + typename
        return fun(casenr)

    def fetch_multi(self, typename, testcases):
        return [(i, self.fetch_one(typename, i))
                for (s, e) in testcases
                for i in range(s, e + 1)]

    def all_typenames(self):
        return self.type2tdgen.keys()

    def generate_testdata(self):
        for assigncompos in dependency_sort(self.semamod.assignments):
            for assign in assigncompos:
                if type(assign) != TypeAssignment:
                    # ValueAssignment: generate_values()
                    continue
                self.process_TypeAssignment(assign)

    def process_TypeAssignment(self, node):
        self.type2tdgen[node.type_name] = self.generate_tdgen(node.type_decl)

    def generate_tdgen(self, node, **subarg):
        # DEBUG# sys.stderr.write ('Node = ' + str (node) + '\n')
        tnm = type(node)
        if tnm not in self.funmap_tdgen.keys():
            raise Exception('Failure to generate a python type for ' + str(tnm))
        return self.funmap_tdgen[tnm](node, **subarg)

    def tdgenDefinedType(self, node, **subarg):
        modnm = node.module_ref
        if modnm is None:
            syms = self.semamod.imports.imports
            for mod in syms.keys():
                if node.type_name in syms[mod]:
                    modnm = str(mod).lower()
                    break
        if modnm is None:
            modnm = self.unit.lower()
        if not modnm in self.refmods:
            raise Exception('Module name "%s" not found' % modnm)
        thetype = self.refmods[modnm].user_types()[node.type_name]
        return self.generate_tdgen(thetype, **subarg)

    def der_prefixhead(self, tag, body):
        blen = len(body)
        if blen == 0:
            lenh = chr(0)
        elif blen <= 127:
            lenh = chr(blen)
        else:
            lenh = ''
            while blen > 0:
                lenh = chr(blen % 256) + lenh
                blen >>= 8
            lenh = chr(0x80 + len(lenh)) + lenh
        return chr(tag) + lenh + body

    simple_cases = {
        'BOOLEAN': ['\x01\x01\x00', '\x01\x01\xff'],
        'INTEGER': ['\x02\x00', '\x02\x01\x80', '\x02\x01\x01',
                    '\x02\x01\xc0', '\x02\x04\x80\x00\x00\x00',
                    '\x02\x04\xc0\x00\x00\x00'],
        'BITSTRING': ['\x03\x01\x00', '\x03\x02\x00\x01',
                      '\x03\x02\x00\xff', '\x03\x02\x00\xff',
                      '\x03\x02\x01\x7e', '\x03\x02\x07\x80'],
        'OCTETSTRING': ['\x04\x00', '\x04\x04ABCD', '\x04\x04A\x00CD',
                        '\x04\x05ABCD\x00'],
        'NULL': ['\x05\x00', '\x05\x04ABCD'],
        'OBJECTIDENTIFIER': ['\x06\x03\x55\x04\x06', '\x06\x03\x29\x29'],
        'REAL': ['\x09\x00', '\x09\x04ABCD'],
        'ENUMERATED': ['\x0a\x00', '\x0a\x01\x01', '\x0a\x03\x12\x34\x56'],
        'UTF8STRING': ['\x0c\x00', '\x0c\x01\x7f',
                       '\x0c\x02\xc0\xc0', '\x0c\x02\xdf\xff',
                       '\x0c\x03\xe0\x80\x80', '\x0c\x03\xef\xbf\xbf',
                       '\x0c\x04\xf0\x00\x00\x00',
                       '\x0c\x04\xf7\xbf\xbf\xbf'],
        'SEQUENCE': ['\x30\x00'],
        'SET': ['\x31\x00'],
        'IA5STRING': ['\x16\x00', '\x16\x04ABCD'],
        'UTCTIME': ['\x17\x0d200207235959Z'],
        'GENERALIZEDTIME': ['\x18\x0e20001231235959',
                            '\x18\x1220001231235959.999',
                            '\x18\x1320001231205959.999Z'],
        'GENERALSTRING': ['\x1b\x00'],
        'UNIVERSALSTRING': ['\x1c\x00'],
    }

    def tdgenSimple(self, node):
        # Simple types are generate from builtin lists "simple_cases"
        cases = self.simple_cases[
            node.type_name.replace(' ', '').upper()]

        def do_gen(casenr):
            assert casenr < len(cases), 'Simple type case number out of range'
            return cases[casenr]

        return len(cases), do_gen

    def tdgenNamedType(self, node, **subarg):
        # Ignore the name label and delegate to the declared type
        return self.generate_tdgen(node.type_decl, **subarg)

    nodeclass2basaltag = {
        'APPLICATION': api.DER_PACK_ENTER | api.DER_TAG_APPLICATION(0),
        'CONTEXT': api.DER_PACK_ENTER | api.DER_TAG_CONTEXT(0),
        'PRIVATE': api.DER_PACK_ENTER | api.DER_TAG_PRIVATE(0)
    }

    def tdgenTagged(self, node, implicit_tag=None):
        # Tagged values delegate to type_decl, prefixing a header
        (subcnt, subgen) = self.generate_tdgen(node.type_decl)
        am_implicit = self.semamod.resolve_tag_implicitness(node.implicitness, node.type_decl) == TagImplicitness.IMPLICIT
        tag = self.nodeclass2basaltag[node.class_name or 'CONTEXT']
        tag |= int(node.class_number)

        def do_gen(casenr):
            if am_implicit:
                retval = subgen(casenr, implicit_tag=tag)
            else:
                retval = subgen(casenr)
                retval = self.der_prefixhead(tag, retval)
            if implicit_tag is not None:
                retval = self.der_prefixhead(implicit_tag, retval)
            return retval

        return subcnt, do_gen

    def tdgenChoice(self, node, implicit_tag=None):
        """CHOICE test cases are generated by enabling each of the
           choices in turn.  Initially, this yields the (0) choice.
           On further rounds, alternatives within each of the
           choices are addressed.  This implements the width-first
           approach, by iterating over the choices first, and only
           within that allow for iteration within the choices.
        """
        elcnts = []
        elgens = []
        for comp in node.components:
            if isinstance(comp, ExtensionMarker):
                # TODO# ...ASN.1 extensions...
                continue
            if isinstance(comp, ComponentType) and comp.components_of_type is not None:
                # TODO# ...COMPONENTS OF...
                continue
            (c, g) = self.generate_tdgen(comp.type_decl)
            elcnts.append(c)
            elgens.append(g)
        # Derive how many elements change in any given round
        round2flips = []
        for e in range(max(elcnts)):
            round2flips.append(len([e
                                    for e in elcnts
                                    if e > len(round2flips)]))
        # Total cases iterate over element cases, but trivialise first
        totcnt = sum(elcnts)

        def do_gen(casenr):
            # Index-specific generator for tdgenChoice
            round_ = 0
            # Invariants for the following loop:
            #  - We have made "round" passes over all components
            #  - Considering that some components end before others
            #  - We still have to generate "casenr" new values
            #  - Skips for "round" are in "elcnts_sorted[round]"
            while casenr >= round2flips[round_]:
                casenr -= round2flips[round_]
                round_ += 1
            eltidx = 0
            # Invariants for the following loop:
            #  - We have made "round" passes over all components
            #  - Considering that some components end before others
            #  - We still have to generate "casenr" new values
            #  - The current "round" contains new "casenr" value
            #  - Searching for "eltidx" for the value to generate
            while True:
                if elcnts[eltidx] > round_:
                    if casenr == 0:
                        break
                    casenr -= 1
                eltidx += 1
            # Current knowledge:
            #  - We reduced "casenr" to 0 in "round" at "eltidx"
            #  - We have made "round" passes over all components
            #  - We have found "eltidx" to generate
            #  - We should deliver eltgen(round) for "eltidx"
            #  - We should deliver eltgen(0) for all but "eltidx"
            retval = elgens[eltidx](round_)
            if implicit_tag is not None:
                retval = self.der_prefixhead(implicit_tag, retval)
            return retval

        return totcnt, do_gen

    def tdgenConstructed(self, node, implicit_tag=None):
        """SEQUENCE and SET test cases are generated assuming
           that the fields are orthogonal.  This means that not all
           combinations of all fields are formed.  The search is
           however width-first, meaning that it does not pass through
           all values of the first field before continuing to the
           next, but instead it will cycle over the fields.  While
           experimenting with a field, the other fields are set to
           their 0 value, for simplicity's sake.

           TODO: Missing support for OPTIONAL / DEFAULT cases
        """
        elcnts = []
        elgens = []
        for comp in node.components:
            if isinstance(comp, ExtensionMarker):
                # TODO# ...ASN.1 extensions...
                continue
            if isinstance(comp, ComponentType) and comp.components_of_type is not None:
                # TODO# ...COMPONENTS OF...
                continue
            (c, g) = self.generate_tdgen(comp.type_decl)
            elcnts.append(c)
            elgens.append(g)
        # Derive how many elements change in any given round
        round2flips = []
        for e in range(max(elcnts)):
            round2flips.append(len([e
                                    for e in elcnts
                                    if e > len(round2flips)]))
        # Total cases iterate over element cases, but trivialise first
        totcnt = 1 + sum(elcnts) - len(elcnts)
        # Comp will be filled with all eltgen(0) values
        comp = [None] * len(elgens)
        if implicit_tag is not None:
            tag = implicit_tag
        elif type(node) == SetType:
            tag = 0x31
        else:
            tag = 0x30

        def do_gen(casenr):
            # Index-specific generator for tdgenConstructed
            # TODO# if comp is None:
            if None in comp:
                for idx2 in range(len(elgens)):
                    comp[idx2] = elgens[idx2](0)
            round_ = 0
            # Invariants for the following loop:
            #  - We have made "round" passes over all components
            #  - Considering that some components end before others
            #  - We still have to generate "casenr" new values
            #  - Skips for "round" are in "elcnts_sorted[round]"
            while casenr >= round2flips[round_]:
                casenr -= round2flips[round_]
                round_ += 1
            eltidx = 0
            # Invariants for the following loop:
            #  - We have made "round" passes over all components
            #  - Considering that some components end before others
            #  - We still have to generate "casenr" new values
            #  - The current "round" contains new "casenr" value
            #  - Searching for "eltidx" for the value to generate
            while True:
                if elcnts[eltidx] > round_:
                    if casenr == 0:
                        break
                    casenr -= 1
                eltidx += 1
            # Current knowledge:
            #  - We reduced "casenr" to 0 in "round" at "eltidx"
            #  - We have made "round" passes over all components
            #  - We have found "eltidx" to generate
            #  - We should deliver eltgen(round) for "eltidx"
            #  - We should deliver eltgen(0) for all but "eltidx"
            retval = comp[:eltidx]
            if round_ > 0:
                retval += elgens[eltidx](round_)
                eltidx += 1
            retval += comp[eltidx:]
            retval = ''.join(retval)
            retval = self.der_prefixhead(tag, retval)
            return retval

        return totcnt, do_gen

    def tdgenRepeated(self, node, **subarg):
        # SEQUENCE OF and SET OF consist of 0,1,2 entries
        (subcnt, subgen) = self.generate_tdgen(node.type_decl, **subarg)
        totcnt = 1 + subcnt + (subcnt * subcnt)
        tag = 0x31 if type(node) == SetOfType else 0x30

        def do_gen(casenr):
            if casenr == 0:
                retval = ''
            else:
                casenr -= 1
                retval = subgen(casenr % subcnt)
                if casenr >= subcnt:
                    casenr -= subcnt
                    retval = retval + subgen(casenr / subcnt)
            retval = self.der_prefixhead(tag, retval)
            return retval

        return totcnt, do_gen
