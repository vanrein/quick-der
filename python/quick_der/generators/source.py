from six import StringIO
from os import path
import logging

logger = logging.getLogger(__name__)

from asn1ate.sema import DefinedType, ValueAssignment, TypeAssignment, TaggedType, SimpleType, BitStringType, \
    ValueListType, SequenceType, SetType, ChoiceType, SequenceOfType, SetOfType, ComponentType, dependency_sort


from quick_der.util import tosym
from quick_der.generators import QuickDERgeneric


class QuickDER2source(QuickDERgeneric):

    def __init__(self, semamod, outfn, refmods):
        self.to_be_defined = None
        self.to_be_overlaid = None
        self.cursor_offset = None
        self.nested_typerefs = None
        self.nested_typecuts = None

        self.semamod = semamod
        self.refmods = refmods

        self.buffer = StringIO()
        self.linebuffer = StringIO()

        self.comma1 = None
        self.comma0 = None

        self.unit, curext = path.splitext(outfn)

        # typedef b a adds a: b to this dict, to weed out dups
        self.issued_typedefs = {}

        # Setup function maps
        self.pack_funmap = {
            DefinedType: self.packDefinedType,
            ValueAssignment: self.packValueAssignment,
            TypeAssignment: self.packTypeAssignment,
            TaggedType: self.packTaggedType,
            SimpleType: self.packSimpleType,
            BitStringType: self.packSimpleType,
            ValueListType: self.packSimpleType,
            SequenceType: self.packSequenceType,
            SetType: self.packSetType,
            ChoiceType: self.packChoiceType,
            SequenceOfType: self.packRepeatingStructureType,
            SetOfType: self.packRepeatingStructureType,
            ComponentType: self.packSimpleType,
        }

    def write(self, txt):
        self.buffer.write(txt)
        self.linebuffer.write(txt)

    def writeln(self, txt=''):
        self.buffer.write(txt + '\n')
        self.linebuffer.write(txt)
        logger.info(self.linebuffer.getvalue())
        self.linebuffer.truncate(0)
        self.linebuffer.seek(0)

    def close(self):
        pass

    def generate_head(self):
        pass

    def generate_tail(self):
        pass

    def generate_unpack(self):
        pass

    def generate_pack(self):
        for assigncompos in dependency_sort(self.semamod.assignments):
            for assign in assigncompos:
                self.generate_pack_node(assign, None, None)

    def generate_pack_node(self, node, tp, fld):
        tnm = type(node)
        if tnm in self.pack_funmap:
            self.pack_funmap[tnm](node, tp, fld)

    def packValueAssignment(self, node, tp, fld):
        pass

    def packDefinedType(self, node, tp, fld):
        pass

    def packSimpleType(self, node, tp, fld):
        pass

    def packTypeAssignment(self, node, tp, fld):
        # Issue each typedef b a only once, because -- even if you
        # use the same b, a each time -- type-redefinition is a C11
        # feature, which isn't what we want.
        # self.to_be_overlaid is a list of (tname,tdecl) pairs to be created
        self.to_be_defined = []
        self.to_be_overlaid = [(tosym(node.type_name), node.type_decl)]
        while len(self.to_be_overlaid) > 0:
            (tname, tdecl) = self.to_be_overlaid.pop(0)
            key = (self.unit, tname)
            if key not in self.issued_typedefs:
                self.issued_typedefs[key] = str(tdecl)

                self.writeln('KeehiveError')
                self.writeln('DER_PACK_{}('.format(tname))
                self.writeln('){')
                #self.generate_pack_node(tdecl, tname, '0')
                self.writeln(')}')
                self.writeln()

                self.writeln('KeehiveError')
                self.writeln('DER_UNPACK_{}('.format(tname))
                self.writeln('){')
                #self.generate_pack_node(tdecl, tname, '0')
                self.writeln(')}')
                self.writeln()


            else:
                if self.issued_typedefs[key] != str(tdecl):
                    raise TypeError("Redefinition of type %s." % key[1])
        for tbd in self.to_be_defined:
            if tbd != 'DER_OVLY_' + self.unit + '_' + tosym(node.type_name) + '_0':
                self.writeln('typedef struct ' + tbd + ' ' + tbd + ';')
        self.writeln()

    def packSequenceType(self, node, tp, fld, naked=False):
        pass

    def packSetType(self, node, tp, fld, naked=False):
        pass

    def packChoiceType(self, node, tp, fld, naked=False):
        pass

    def packRepeatingStructureType(self, node, tp, fld):
        pass

    def packTaggedType(self, node, tp, fld):
        pass