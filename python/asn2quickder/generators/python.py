from asn1ate.sema import DefinedType, SimpleType, BitStringType, ValueListType, NamedType, TaggedType, ChoiceType, \
    SequenceType, SetType, SequenceOfType, SetOfType, dependency_sort, ValueAssignment, NameForm, NumberForm, \
    NameAndNumberForm, TypeAssignment, TagImplicitness, ExtensionMarker, ComponentType

from asn2quickder import packstx as api
from asn2quickder.util import api_prefix, dertag2atomsubclass
from asn2quickder.generators import QuickDERgeneric
from asn2quickder.util import tosym


class QuickDER2py(QuickDERgeneric):
    """Generate Python modules with Quick DER definitions, based on
       generic definitions in the asn2quickder module.  The main task of
       this generator is to provide class definitions that subclass
       ASN1Object (usually through an intermediate subclass such as
       ASN1StructuredType) and can be invoked with a binary string
       holding DER-encoded data, or without any argument to create
       an empty structure.  The resulting classes support both the
       der_pack() and der_unpack() operations.  See PYTHON.MD!

       The recursion model strives for two, overlapping, goals and
       must therefore be stopped explicitly.  First, it constructs
       packer code up to a SEQUENCE OF or SET OF or ANY and cannot
       support recursion (yet).  This form of recursion can stop as
       soon as any of the packer-terminal codes is reached, but it
       needs to follow type references via DefinedType elements.
       The second reason for recursion is to produce class code,
       and this passes through SEQUENCE OF and SET OF (but not ANY)
       to complete the class definition.  It does not need to
       traverse to other classes by following DefinedType elements,
       however.  Each of these discards certain information from
       their continued explorations, and when both kinds of
       traversal were crossed, the data would only be collected to
       be discarded.  This can be avoided by knowing whether both
       forms have been crossed, and stopping the further traversal
       if this is indeed the case.  In terms of code, once the
       execution reaches a point where it would set one flag, it
       would check the other flag and return trivially if this
       is already/also set.  Flags are only raised for the
       duration of the recursive traversal, and they may be set
       multiple times before the other flag is set, so they are
       subjected to a stack-based regimen -- or, even simpler,
       to nesting counters.  The first form is managed with
       nested_typecuts, the second with nested_typerefs.
    """

    def __init__(self, semamod, outfn, refmods):
        self.cursor_offset = None
        self.nested_typerefs = None
        self.nested_typecuts = None

        self.semamod = semamod
        self.refmods = refmods

        # Open the output file
        super(QuickDER2py, self).__init__(outfn, '.py')
        # Setup the function maps for generating Python
        self.funmap_pytype = {
            DefinedType: self.pytypeDefinedType,
            SimpleType: self.pytypeSimple,
            BitStringType: self.pytypeSimple,
            ValueListType: self.pytypeSimple,
            NamedType: self.pytypeNamedType,
            TaggedType: self.pytypeTagged,
            ChoiceType: self.pytypeChoice,
            SequenceType: self.pytypeSequence,
            SetType: self.pytypeSet,
            SequenceOfType: self.pytypeSequenceOf,
            SetOfType: self.pytypeSetOf,
        }

    def comment(self, text):
        for ln in str(text).split('\n'):
            self.writeln('# ' + ln)

    def generate_head(self):
        self.writeln('#')
        self.writeln('# asn2quickder output for ' + self.semamod.name + ' -- automatically generated')
        self.writeln('#')
        self.writeln('# Read more about Quick `n\' Easy DER on https://github.com/vanrein/quick-der')
        self.writeln('#')
        self.writeln()
        self.writeln()
        self.writeln('#')
        self.writeln('# Import general definitions and package dependencies')
        self.writeln('#')
        self.writeln()
        self.writeln('import asn2quickder.api as ' + api_prefix)
        self.writeln()

        if not self.semamod.imports:
            return

        imports = self.semamod.imports.imports
        for rm in imports.keys():
            pymod = tosym(str(rm).rsplit('.', 1)[0]).lower()
            self.write('from ' + pymod + ' import ')
            self.writeln(', '.join(map(tosym, imports[rm])))
        self.writeln()
        self.writeln()

    def generate_tail(self):
        self.writeln()
        self.writeln('# asn2quickder output for ' + self.semamod.name + ' ends here')

    def generate_values(self):
        self.writeln('#')
        self.writeln('# Variables with ASN.1 value assignments')
        self.writeln('#')
        self.writeln()
        for assigncompos in dependency_sort(self.semamod.assignments):
            for assign in assigncompos:
                if type(assign) != ValueAssignment:
                    # TypeAssignemnts: generate_classes()
                    continue
                    # TODO# Need generic mapping to DER values
                self.pygenValueAssignment(assign)

    def pygenValueAssignment(self, node):
        # We only found INTEGER and OBJECTIDENTIFIER in RFCs
        # Note that these forms are computed while loading, so not fast
        cls = tosym(node.type_decl)
        var = tosym(node.value_name)
        if cls == 'INTEGER':
            val = self.pyvalInteger(node.value)
            cls = api_prefix + '.ASN1Integer'
        elif cls == 'OBJECTIDENTIFIER':
            val = self.pyvalOID(node.value)
            cls = api_prefix + '.ASN1OID'
        else:
            val = 'UNDEF_MAP2DER("""' + str(node.value) + '""")'
        self.comment(str(node))
        # Must provide a context for name resolution, even {} will do
        self.writeln(var + ' = ' + cls + ' (bindata=[' + val + '], context={})')
        self.writeln()

    def pyvalInteger(self, valnode):
        return api_prefix + '.der_format_INTEGER (' + str(int(valnode)) + ')'

    def pyvalOID(self, valnode):
        retc = []
        for oidcompo in valnode.components:
            if type(oidcompo) == NameForm:
                retc.append(api_prefix + '.der_parse_OID (' + tosym(oidcompo.name) + '.get())')
            elif type(oidcompo) == NumberForm:
                retc.append("'" + str(oidcompo.value) + "'")
            elif type(oidcompo) == NameAndNumberForm:
                retc.append("'" + str(oidcompo.number) + "'")
        retval = " + '.' + ".join(retc)
        retval = api_prefix + '.der_format_OID (' + retval.replace("' + '", '') + ')'
        return retval

    def generate_classes(self):
        self.writeln('#')
        self.writeln('# Classes for ASN.1 type assignments')
        self.writeln('#')
        self.writeln()
        for assigncompos in dependency_sort(self.semamod.assignments):
            for assign in assigncompos:
                if type(assign) != TypeAssignment:
                    # ValueAssignment: generate_values()
                    continue
                self.pygenTypeAssignment(assign)

    def pygenTypeAssignment(self, node):

        def pymap_packer(pck, ln='\n        '):
            retval = '(' + ln
            pck = pck + ['DER_PACK_END']
            comma = ''
            for pcke in pck:
                pcke = pcke.replace('DER_', api_prefix + '.DER_')
                retval += comma + 'chr(' + pcke + ')'
                comma = ' +' + ln
            retval += ' )'
            return retval

        def pymap_recipe(recp, ctxofs, ln='\n    '):
            if type(recp) == int:
                retval = str(recp + ctxofs)
            elif recp[0] == '_NAMED':
                (_NAMED, map_) = recp
                ln += '    '
                retval = "('_NAMED', {"
                comma = False
                for (fld, fldrcp) in map_.items():
                    if comma:
                        retval += ',' + ln
                    else:
                        retval += ln
                    retval += "'" + tosym(fld) + "': "
                    retval += pymap_recipe(fldrcp, ctxofs, ln)
                    comma = True
                retval += ' } )'
            elif recp[0] in ['_SEQOF', '_SETOF']:
                (_STHOF, allidx, pck, num, inner_recp) = recp
                ln += '    '
                retval = "('" + _STHOF + "', "
                retval += str(allidx) + ', '
                retval += pymap_packer(pck, ln) + ','
                retval += str(num) + ',' + ln
                retval += pymap_recipe(inner_recp, 0, ln) + ' )'
            elif recp[0] == '_TYPTR':
                (_TYPTR, [clsnm], ofs) = recp
                retval = repr(recp)
            else:
                assert False, 'Unexpected recipe tag ' + str(recp[0])
                # retval = repr(recp)
            return retval

        def pygen_class(clsnm, tp, ctxofs, pck, recp, numcrs):
            # TODO# Sometimes, ASN1Atom may have a specific supertp
            supertp = tosym(tp)
            self.writeln('class ' + clsnm + ' (' + supertp + '):')
            atom = type(recp) == int
            subatom = atom and tp != 'ASN1Atom'
            said_sth = False
            if tp not in ['ASN1SequenceOf', 'ASN1SetOf'] and not subatom:
                self.writeln('    _der_packer = ' + pymap_packer(pck))
                said_sth = True
            if not atom:
                self.writeln('    _recipe = ' + pymap_recipe(recp, ctxofs))
                said_sth = True
            if False:
                # TODO# Always fixed or computed
                self.writeln('    _numcursori = ' + str(numcrs))
                said_sth = True
            if not atom:
                self.writeln('    _context = globals ()')
                self.writeln('    _numcursori = ' + str(numcrs))
                said_sth = True
            elif subatom:
                self.writeln('    _context = ' + api_prefix + '.__dict__')
            if not said_sth:
                self.writeln('    pass')
            self.writeln()

        #
        # body of pygenTypeAssignment
        #
        self.cursor_offset = 0
        self.nested_typerefs = 0
        self.nested_typecuts = 0
        self.comment(str(node))
        (pck, recp) = self.generate_pytype(node.type_decl)
        ofs = 0
        tp = None
        if type(recp) == int:
            dertag = eval(pck[0], api.__dict__)
            if dertag in dertag2atomsubclass:
                tp = dertag2atomsubclass[dertag]
            else:
                tp = 'ASN1Atom'
            tp = api_prefix + '.' + tp
        elif recp[0] == '_NAMED':
            tp = api_prefix + '.ASN1ConstructedType'
        elif recp[0] == '_SEQOF':
            tp = api_prefix + '.ASN1SequenceOf'
        elif recp[0] == '_SETOF':
            tp = api_prefix + '.ASN1SetOf'
        elif recp[0] == '_TYPTR':
            (_TYPTR, [cls], ofs) = recp
            tp = str(cls)
            # TODO:GONE# if tp [:len(api_prefix)+1] == api_prefix + '.':
            # TODO:GONE# 	# Strip off api_prefix to avoid duplication
            # TODO:GONE# 	tp = tp [len(api_prefix)+1:]
        else:
            assert False, 'Unknown recipe tag ' + str(recp[0])
        numcrs = self.cursor_offset
        pygen_class(tosym(node.type_name), tp, ofs, pck, recp, numcrs)

    def generate_pytype(self, node, **subarg):
        # DEBUG# sys.stderr.write ('Node = ' + str (node) + '\n')
        tnm = type(node)
        if tnm not in self.funmap_pytype.keys():
            raise Exception('Failure to generate a python type for ' + str(tnm))
        return self.funmap_pytype[tnm](node, **subarg)

    def pytypeDefinedType(self, node, **subarg):
        modnm = node.module_ref
        if not modnm and self.semamod.imports:
            syms = self.semamod.imports.imports
            for mod in syms.keys():
                if node.type_name in syms[mod]:
                    modnm = str(mod).lower()
                    break
        if modnm is None:
            modnm = self.unit.lower()
        if modnm not in self.refmods:
            raise Exception('Module name "%s" not found' % modnm)
        popunit = self.unit
        popsema = self.semamod
        popcofs = self.cursor_offset
        self.unit = modnm
        self.semamod = self.refmods[modnm]
        # TODO:BAD# self.cursor_offset = 0
        if self.nested_typecuts > 0:
            self.nested_typerefs += 1
        thetype = self.refmods[modnm].user_types()[node.type_name]
        (pck, recp) = self.generate_pytype(thetype, **subarg)
        # if self.nested_typecuts > 0:
        if True:
            recp = ('_TYPTR', [node.type_name], popcofs)
            self.nested_typerefs -= 1
            # TODO:BAD# self.cursor_offset += popcofs
        self.semamod = popsema
        self.unit = popunit
        return pck, recp

    def pytypeSimple(self, node, implicit_tag=None):
        simptp = node.type_name.replace(' ', '').upper()
        if simptp == 'ANY':
            # ANY counts as self.nested_typecuts but does not
            # have subtypes to traverse, so no attention to
            # recursion cut-off is needed or even possible here
            pck = ['DER_PACK_ANY']
            simptag = api.DER_PACK_ANY
            if implicit_tag:
                # Can't have an implicit tag around ANY
                pck = ['DER_PACK_ENTER | ' + implicit_tag] + pck + ['DER_PACK_LEAVE']
        else:
            if not implicit_tag:
                implicit_tag = 'DER_TAG_' + simptp
            pck = ['DER_PACK_STORE | ' + implicit_tag]
            simptag = eval('DER_TAG_' + simptp, api.__dict__)
        recp = self.cursor_offset
        self.cursor_offset += 1
        if simptag in dertag2atomsubclass:
            recp = ('_TYPTR', [api_prefix + '.' + dertag2atomsubclass[simptag]], recp)
        return pck, recp

    def pytypeTagged(self, node, implicit_tag=None):
        mytag = 'DER_TAG_' + (node.class_name or 'CONTEXT') + '(' + node.class_number + ')'
        if self.semamod.resolve_tag_implicitness(node.implicitness, node.type_decl) == TagImplicitness.IMPLICIT:
            # Tag implicitly by handing mytag down to type_decl
            (pck, recp) = self.generate_pytype(node.type_decl,
                                               implicit_tag=mytag)
        else:
            # Tag explicitly by wrapping mytag around the type_decl
            (pck, recp) = self.generate_pytype(node.type_decl)
            pck = ['DER_PACK_ENTER | ' + mytag] + pck + ['DER_PACK_LEAVE']
        if implicit_tag:
            # Can't nest implicit tags, so wrap surrounding ones
            pck = ['DER_PACK_ENTER | ' + implicit_tag] + pck + ['DER_PACK_LEAVE']
        return pck, recp

    def pytypeNamedType(self, node, **subarg):
        # TODO# Ignore field name... or should we use it any way?
        return self.generate_pytype(node.type_decl, **subarg)

    def pyhelpConstructedType(self, node):
        pck = []
        recp = {}
        for comp in node.components:
            if isinstance(comp, ExtensionMarker):
                # TODO# ...ASN.1 extensions...
                continue
            if isinstance(comp, ComponentType) and comp.components_of_type is not None:
                # TODO# ...COMPONENTS OF...
                continue
            (pck1, stru1) = self.generate_pytype(comp.type_decl)
            if isinstance(comp, ComponentType):
                if comp.optional or comp.default_value:
                    pck1 = ['DER_PACK_OPTIONAL'] + pck1
            pck = pck + pck1
            recp[tosym(comp.identifier)] = stru1
        return pck, ('_NAMED', recp)

    def pytypeChoice(self, node, implicit_tag=None):
        (pck, recp) = self.pyhelpConstructedType(node)
        pck = ['DER_PACK_CHOICE_BEGIN'] + pck + ['DER_PACK_CHOICE_END']
        if implicit_tag:
            # Can't have an implicit tag around a CHOICE
            pck = ['DER_PACK_ENTER | ' + implicit_tag] + pck + ['DER_PACK_LEAVE']
        return pck, recp

    def pytypeSequence(self, node, implicit_tag='DER_TAG_SEQUENCE'):
        (pck, recp) = self.pyhelpConstructedType(node)
        pck = ['DER_PACK_ENTER | ' + implicit_tag] + pck + ['DER_PACK_LEAVE']
        return pck, recp

    def pytypeSet(self, node, implicit_tag='DER_TAG_SET'):
        (pck, recp) = self.pyhelpConstructedType(node)
        pck = ['DER_PACK_ENTER | ' + implicit_tag] + pck + ['DER_PACK_LEAVE']
        return pck, recp

    def pyhelpRepeatedType(self, node, dertag, recptag):
        allidx = self.cursor_offset
        self.cursor_offset += 1
        if self.nested_typerefs > 0 and self.nested_typecuts > 0:
            # We are about to recurse on self.nested_typecuts
            # but the recursion for self.nested_typerefs
            # has also occurred, so we can cut off recursion
            subpck = ['DER_ERROR_RECURSIVE_USE_IN' + recptag]
            subrcp = ('_ERROR', 'Recursive use in ' + recptag)
            subnum = 0
        else:
            self.nested_typecuts = self.nested_typecuts + 1
            popcofs = self.cursor_offset
            self.cursor_offset = 0
            (subpck, subrcp) = self.generate_pytype(node.type_decl)
            subnum = self.cursor_offset
            self.cursor_offset = popcofs
            self.nested_typecuts = self.nested_typecuts - 1
        pck = ['DER_PACK_STORE | ' + dertag]
        return pck, (recptag, allidx, subpck, subnum, subrcp)

    def pytypeSequenceOf(self, node, implicit_tag='DER_TAG_SEQUENCE'):
        return self.pyhelpRepeatedType(node, implicit_tag, '_SEQOF')

    def pytypeSetOf(self, node, implicit_tag='DER_TAG_SET'):
        return self.pyhelpRepeatedType(node, implicit_tag, '_SETOF')
