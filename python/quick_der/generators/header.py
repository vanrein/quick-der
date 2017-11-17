from asn1ate.sema import DefinedType, ValueAssignment, TypeAssignment, TaggedType, SimpleType, BitStringType, \
    ValueListType, SequenceType, SetType, ChoiceType, SequenceOfType, SetOfType, ComponentType, dependency_sort, \
    TagImplicitness, ExtensionMarker, NamedType

from quick_der.util import tosym, dprint
from quick_der.generators import QuickDERgeneric


class QuickDER2c(QuickDERgeneric):
    """Generate the C header files for Quick DER, a.k.a. Quick and Easy DER.

       There are two things that are generated for each of the ASN.1 syntax
       declaration symbol of a unit:

       #define DER_PACK_unit_SyntaxDeclSym \
            DER_PACK_ENTER | ..., \
            DER_sub1..., \
            DER_sub2..., \
            DER_PACK_LEAVE

       this is a walking path for the der_pack() and der_unpack() instructions.

       At a later point, we decided to split the definitions to be able to
       support IMPLICIT TAGS (such as used with LDAP).  This is a matter of
       separating out anything but the outisde element of a named definition:

       #define DER_PIMP_unit_SyntaxDeclSym(implicit_tag) \
            DER_PACK_ENTER | implicit_tag, \
            DER_sub1..., \
            DER_sub2..., \
            DER_PACK_LEAVE

       #define DER_PACK_unit_SyntaxDeclSym \
            DER_PACK_ENTER | DER_PACK_SEQUENCE, \
            DER_sub1 ..., \
            DER_sub2 ..., \
            DER_PACK_LEAVE

       This makes implicit tags available over an additional symbol.
       And of course, this form is now referenced when calling for it.

       Note that packing paths do not have a closing DER_PACK_END, it is
       easy to forget that but it really improves packer flexibility.

       In addition, there will be a struct for each of the symbols:

       struct unit_SyntaxDeclSym_overlay {
           dercursor field1;
           dercursor field2;
           struct unit_EmbeddedSym_overlay field3;
           dercursor field4;
       };

       The unit prefix will be set to the filename of the module, usually
       something like rfc5280 when the parsed file is rfc5280.asn1 and the
       output is then written to rfc5280.h for easy inclusion by the C code.
    """

    def __init__(self, semamod, outfn, refmods):
        self.to_be_defined = None
        self.to_be_overlaid = None
        self.cursor_offset = None
        self.nested_typerefs = None
        self.nested_typecuts = None

        self.semamod = semamod
        self.refmods = refmods

        # Open the output file
        super(QuickDER2c, self).__init__(outfn, '.h')
        # Setup function maps
        self.overlay_funmap = {
            DefinedType: self.overlayDefinedType,
            ValueAssignment: self.overlayValueAssignment,
            TypeAssignment: self.overlayTypeAssignment,
            TaggedType: self.overlayTaggedType,
            SimpleType: self.overlaySimpleType,
            BitStringType: self.overlaySimpleType,
            ValueListType: self.overlaySimpleType,
            SequenceType: self.overlayConstructedType,
            SetType: self.overlayConstructedType,
            ChoiceType: self.overlayConstructedType,
            SequenceOfType: self.overlayRepeatingStructureType,
            SetOfType: self.overlayRepeatingStructureType,
            ComponentType: self.overlaySimpleType,  # TODO#
        }
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
            SequenceOfType: self.packSequenceOfType,
            SetOfType: self.packSetOfType,
            ComponentType: self.packSimpleType,  # TODO#
        }
        self.psub_funmap = {
            DefinedType: self.psubDefinedType,
            ValueAssignment: self.psubValueAssignment,
            TypeAssignment: self.psubTypeAssignment,
            TaggedType: self.psubTaggedType,
            SimpleType: self.psubSimpleType,
            BitStringType: self.psubSimpleType,
            ValueListType: self.psubSimpleType,
            SequenceType: self.psubConstructedType,
            SetType: self.psubConstructedType,
            ChoiceType: self.psubConstructedType,
            SequenceOfType: self.psubRepeatingStructureType,
            SetOfType: self.psubRepeatingStructureType,
            ComponentType: self.psubSimpleType,  # TODO#
        }
        self.issued_typedefs = {}  # typedef b a adds a: b to this dict, to weed out dups

    def generate_head(self):
        self.writeln('/*')
        self.writeln(' * asn2quickder output for ' + self.semamod.name + ' -- automatically generated')
        self.writeln(' *')
        self.writeln(' * Read more about Quick `n\' Easy DER on https://github.com/vanrein/quick-der')
        self.writeln(' *')
        self.writeln(' */')
        self.writeln()
        self.writeln()
        self.writeln('#ifndef QUICK_DER_' + self.unit + '_H')
        self.writeln('#define QUICK_DER_' + self.unit + '_H')
        self.writeln()
        self.writeln()
        self.writeln('#include <quick-der/api.h>')
        self.writeln()
        self.writeln()
        closer = ''
        rmfns = set()

        if not self.semamod.imports:
            return

        for rm in self.semamod.imports.imports.keys():
            rmfns.add(tosym(str(rm).rsplit('.', 1)[0]).lower())

        for rmfn in rmfns:
            self.writeln('#include <quick-der/' + rmfn + '.h>')
            closer = '\n\n'
        self.write(closer)
        closer = ''

        for rm in self.semamod.imports.imports.keys():
            rmfn = tosym(str(rm).rsplit('.', 1)[0]).lower()
            for sym in self.semamod.imports.imports[rm]:
                self.writeln('typedef DER_OVLY_' + tosym(rmfn) + '_' + tosym(sym) + ' DER_OVLY_' + tosym(
                    self.unit) + '_' + tosym(sym) + ';')
                closer = '\n\n'
        self.write(closer)
        closer = ''

        for rm in self.semamod.imports.imports.keys():
            rmfn = tosym(str(rm).rsplit('.', 1)[0]).lower()
            for sym in self.semamod.imports.imports[rm]:
                self.writeln(
                    '#define DER_PIMP_' + tosym(self.unit) + '_' + tosym(sym) + '(implicit_tag) DER_PIMP_' + tosym(
                        rmfn) + '_' + tosym(sym) + '(implicit_tag)')
                self.writeln()
                self.writeln('#define DER_PACK_' + tosym(self.unit) + '_' + tosym(sym) + ' DER_PACK_' + tosym(
                    rmfn) + '_' + tosym(sym) + '')
                closer = '\n\n'
        self.write(closer)

    def generate_tail(self):
        self.writeln()
        self.writeln()
        self.writeln('#endif /* QUICK_DER_' + self.unit + '_H */')
        self.writeln()
        self.writeln()
        self.writeln('/* asn2quickder output for ' + self.semamod.name + ' ends here */')

    def generate_overlay(self):
        self.writeln()
        self.writeln()
        self.writeln('/* Overlay structures with ASN.1 derived nesting and labelling */')
        self.writeln()
        for assigncompos in dependency_sort(self.semamod.assignments):
            for assign in assigncompos:
                self.generate_overlay_node(assign, None, None)

    def generate_pack(self):
        self.writeln()
        self.writeln()
        self.writeln('/* Parser definitions in terms of ASN.1 derived bytecode instructions */')
        self.writeln()
        for assigncompos in dependency_sort(self.semamod.assignments):
            for assign in assigncompos:
                tnm = type(assign)
                if tnm in self.pack_funmap:
                    self.pack_funmap[tnm](assign)
                else:
                    raise Exception('No pack generator for ' + str(tnm))

    def generate_psub(self):
        self.writeln()
        self.writeln()
        self.writeln('/* Recursive parser-sub definitions in support of SEQUENCE OF and SET OF */')
        self.writeln()
        for assigncompos in dependency_sort(self.semamod.assignments):
            for assign in assigncompos:
                tnm = type(assign)
                if tnm in self.psub_funmap:
                    dprint('Recursive call for', tnm)
                    self.psub_funmap[tnm](assign, None, None, True)
                    dprint('Recursion done for', tnm)
                else:
                    raise Exception('No psub generator for ' + str(tnm))

    def generate_psub_sub(self, node, subquads, tp, fld):
        if fld is None:
            fld = ''
        else:
            fld = '_' + fld
        # OLD:TEST:TODO# mod = node.module_ref or self.unit
        mod = self.unit
        self.comma()
        self.writeln('const struct der_subparser_action DER_PSUB_' + mod + '_' + tp + fld + ' [] = { \\')
        for (idx, esz, pck, sub) in subquads:
            self.writeln('\t\t{ ' + str(idx) + ', \\')
            self.writeln('\t\t  ' + str(esz) + ', \\')
            self.writeln('\t\t  ' + pck + ', \\')
            self.writeln('\t\t  ' + sub + ' }, \\')
        self.writeln('\t\t{ 0, 0, NULL, NULL } \\')
        self.write('\t}')

    def generate_overlay_node(self, node, tp, fld):
        tnm = type(node)
        if tnm in self.overlay_funmap:
            self.overlay_funmap[tnm](node, tp, fld)
        else:
            raise Exception('No overlay generator for ' + str(tnm))

    def generate_pack_node(self, node, **kwargs):
        # kwargs usually captures implicit, outer_tag
        tnm = type(node)
        if tnm in self.pack_funmap:
            self.pack_funmap[tnm](node, **kwargs)
        else:
            raise Exception('No pack generator for ' + str(tnm))

    def generate_psub_node(self, node, tp, fld, prim):
        tnm = type(node)
        dprint('generate_psub_node() CALLED ON', tnm)
        if tnm in self.psub_funmap:
            return self.psub_funmap[tnm](node, tp, fld, prim)
        else:
            raise Exception('No psub generator for ' + str(tnm))

    def overlayValueAssignment(self, node, tp, fld):
        pass

    def packValueAssignment(self, node):
        pass

    def psubValueAssignment(self, node, tp, fld, prim):
        return []

    def overlayTypeAssignment(self, node, tp, fld):
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
                self.write('typedef ')
                self.generate_overlay_node(tdecl, tname, '0')
                self.writeln(' DER_OVLY_' + self.unit + '_' + tname + ';')
                self.writeln()
            else:
                if self.issued_typedefs[key] != str(tdecl):
                    raise TypeError("Redefinition of type %s." % key[1])
        for tbd in self.to_be_defined:
            if tbd != 'DER_OVLY_' + self.unit + '_' + tosym(node.type_name) + '_0':
                self.writeln('typedef struct ' + tbd + ' ' + tbd + ';')
        self.writeln()

    def packTypeAssignment(self, node, implicit=False):
        # TODO# Would be nicer to have DER_PACK_ backref to DER_PIMP_
        self.write('#define DER_PIMP_' + self.unit + '_' + tosym(node.type_name) + '(implicit_tag)')
        self.newcomma(', \\\n\t', ' \\\n\t')
        self.generate_pack_node(node.type_decl, implicit=False, outer_tag='implicit_tag')
        self.writeln()
        self.writeln()
        self.write('#define DER_PACK_' + self.unit + '_' + tosym(node.type_name))
        self.newcomma(', \\\n\t', ' \\\n\t')
        self.generate_pack_node(node.type_decl, implicit=False)
        self.writeln()
        self.writeln()

    def psubTypeAssignment(self, node, tp, fld, prim):
        # In lieu of typing context, fld is None; tp probably is too
        self.newcomma('; \\\n\t', '#define DEFINE_DER_PSUB_' + self.unit + '_' + tosym(node.type_name) + ' \\\n\t')
        tp = tosym(node.type_name)
        subquads = self.generate_psub_node(node.type_decl, tp, '0', prim)
        dprint('SUBTRIPLES =', subquads)
        if subquads:
            self.generate_psub_sub(node.type_decl, subquads, tp, None)
            self.write(';\n\n')
        return []

    def overlayDefinedType(self, node, tp, fld):
        mod = node.module_ref or self.unit
        self.write('DER_OVLY_' + tosym(mod) + '_' + tosym(node.type_name))

    def packDefinedType(self, node, implicit=False, outer_tag=None):
        # There should never be anything of interest in outer_tag
        mod = node.module_ref or self.unit
        self.comma()
        if outer_tag is None:
            tagging = 'DER_PACK_'
            param = ''
        else:
            tagging = 'DER_PIMP_'
            param = '(' + outer_tag + ')'
        self.write(tagging + tosym(mod) + '_' + tosym(node.type_name) + param)

    def psubDefinedType(self, node, tp, fld, prim):
        dprint('DefinedType type:', node.type_name, '::', type(node.type_name))
        modnm = node.module_ref
        dprint('AFTER modnm = node.module_ref', modnm)
        if not modnm and self.semamod.imports:
            syms = self.semamod.imports.imports
            dprint('SYMS.KEYS() =', syms.keys())
            for mod in syms.keys():
                if node.type_name in syms[mod]:
                    modnm = str(mod).lower()
                    dprint('AFTER modnm = str(mod).lower ()', modnm)
                    break
        if modnm is None:
            # NOT_IN_GENERAL# modnm = node.module_ref
            modnm = self.unit.lower()
            dprint('AFTER modnm = self.unit.lower ()', modnm)
            dprint('MODNM =', modnm, '::', type(modnm))
            dprint('Referenced module:', modnm, '::', type(modnm))
            dprint('Searching case-insensitively in:', self.refmods.keys())
        if modnm not in self.refmods:
            raise Exception('Module name "%s" not found' % modnm)
        thetype = self.refmods[modnm].user_types()[node.type_name]
        dprint('References:', thetype, '::', type(thetype))
        popunit = self.unit
        popsema = self.semamod
        self.unit = modnm
        self.semamod = self.refmods[modnm]
        tp2 = tosym(node.type_name)
        fld2 = '0'
        subtuples = self.generate_psub_node(thetype, tp2, fld2,
                                            prim and (popunit == self.unit) and (tp == tp2))
        self.semamod = popsema
        self.unit = popunit
        dprint('SUBTUPLES =', subtuples)
        return subtuples

    def overlaySimpleType(self, node, tp, fld):
        self.write('dercursor')

    def packSimpleType(self, node, implicit=False, outer_tag=None):
        if outer_tag is None:
            simptp = node.type_name.replace(' ', '').upper()
            if simptp == 'ANY':
                # exceptional syntax, just the instruction DER_PACK_ANY
                self.comma()
                self.write('DER_PACK_ANY')
                return
            outer_tag = 'DER_TAG_' + simptp
        self.comma()
        self.write('DER_PACK_STORE | ' + outer_tag)

    def psubSimpleType(self, node, tp, fld, prim):
        return []

    def overlayTaggedType(self, node, tp, fld):
        # tag = str(node)
        # tag = tag [:tag.find(']')] + ']'
        # self.write('/* ' + tag + ' */ ')
        # if node.implicity == TagImplicity.IMPLICIT:
        #     tag = tag + ' IMPLICIT'
        # elif node.implicity == TagImplicity.IMPLICIT:
        #     tag = tag + ' EXPLICIT'
        self.generate_overlay_node(node.type_decl, tp, fld)

    def packTaggedType(self, node, implicit=False, outer_tag=None):
        if outer_tag is not None:
            self.comma()
            self.write('DER_PACK_ENTER | ' + outer_tag)
        mytag = 'DER_TAG_' + (node.class_name or 'CONTEXT') + '(' + node.class_number + ')'
        if self.semamod.resolve_tag_implicitness(node.implicitness, node.type_decl) == TagImplicitness.IMPLICIT:
            self.generate_pack_node(node.type_decl, implicit=False, outer_tag=mytag)
        else:
            self.comma()
            self.write('DER_PACK_ENTER | ' + mytag)
            self.generate_pack_node(node.type_decl, implicit=False)
            self.comma()
            self.write('DER_PACK_LEAVE')
        if outer_tag is not None:
            self.comma()
            self.write('DER_PACK_LEAVE')

    def packTaggedType_TODO(self, node, implicit=False):
        if not implicit:
            self.comma()
            self.write('DER_PACK_ENTER | DER_TAG_' + (node.class_name or 'CONTEXT') + '(' + node.class_number + ')')
        implicit_sub = (self.semamod.resolve_tag_implicitness(node.implicitness, node.type_decl) == TagImplicitness.IMPLICIT)
        self.generate_pack_node(node.type_decl, implicit=implicit_sub)
        if not implicit:
            self.comma()
            self.write('DER_PACK_LEAVE')

    def psubTaggedType(self, node, tp, fld, prim):
        return self.generate_psub_node(node.type_decl, tp, fld, prim)

    # Sequence, Set, Choice
    def overlayConstructedType(self, node, tp, fld, naked=False):
        if not naked:
            if fld == '0':
                fld = ''
            else:
                fld = '_' + fld
            self.writeln('struct DER_OVLY_' + self.unit + '_' + tp + fld + ' {')
            if fld:
                self.to_be_defined.append('DER_OVLY_' + self.unit + '_' + tp + fld)
        for comp in node.components:
            if isinstance(comp, ExtensionMarker):
                self.writeln('\t/* ...ASN.1 extensions... */')
                continue
            if isinstance(comp, ComponentType) and comp.components_of_type is not None:
                self.writeln('\t/* COMPONENTS OF TYPE ' + str(comp.components_of_type) + ' */')
                self.writeln('//COMP :: ' + str(dir(comp)))
                self.writeln('//TYPE_DECL == ' + str(comp.type_decl))
                self.writeln('//COMPONENTS_OF_TYPE :: ' + str(dir(comp.components_of_type)))
                self.writeln('//CHILDREN :: ' + str(dir(comp.components_of_type.children)))
                self.writeln('//TODO// Not sure how to get to elements and inline them here')
                # TODO:ARG1=???# self.overlayConstructedType (comp.components_of_type, naked=True)
                continue
            self.write('\t')
            subfld = tosym(comp.identifier)
            self.generate_overlay_node(comp.type_decl, tp, subfld)
            self.writeln(' ' + subfld + '; // ' + str(comp.type_decl))
        if not naked:
            self.write('}')

    # Sequence, Set, Choice
    def psubConstructedType(self, node, tp, fld, prim):
        # Iterate over field names, recursively retrieving quads;
        # add the field's offset to each of the quads, for its holding field
        compquads = []
        for comp in node.components:
            if isinstance(comp, ExtensionMarker):
                continue
            subfld = tosym(comp.identifier)
            dprint('subfld is ', subfld)
            dprint('Generating PSUB node for %s', comp.type_decl.type_name)
            subquads = self.generate_psub_node(comp.type_decl, tp, subfld, prim)
            dprint('Generated  PSUB node for %s', comp.type_decl.type_name)
            dprint('quads are %s', subquads)
            if fld == '0':
                subtp = tp
            else:
                subtp = tp + '_' + fld
                # TODO:TEST# subtp = tp + ('_' + fld if fld else '')
                # TODO:TEST# if subfld != '0':
                # TODO:TEST# if subfld:
            if subfld != '0':
                ofs = 'DER_OFFSET (' + self.unit + ',' + subtp + ',' + subfld + ')'
            else:
                ofs = '0'
            for (idx, esz, pck, psb) in subquads:
                dprint('DEALING WITH', pck)
                if str(idx) == '0':
                    idx = ofs
                else:
                    idx = ofs + ' \\\n\t\t+ ' + str(idx)
                compquads.append((idx, esz, pck, psb))
        dprint('psubConstructedType() RETURNS COMPONENT TRIPLES', compquads)
        return compquads

    def packSequenceType(self, node, implicit=False, outer_tag='DER_TAG_SEQUENCE'):
        if not implicit:
            self.comma()
            self.write('DER_PACK_ENTER | ' + outer_tag)
        for comp in node.components:
            if isinstance(comp, ExtensionMarker):
                # TOOMUCH# self.comma()
                self.write('/* ...ASN.1 extensions... */')
                continue
            if isinstance(comp, ComponentType) and comp.components_of_type is not None:
                # Assuming COMPONENTS OF cannot be OPTIONAL, otherwise move this down
                self.comma()
                self.writeln('DER_PIMP_' + tosym(self.unit) + '_' + tosym(
                    comp.components_of_type.type_name) + '\t/* COMPONENTS OF ' + str(comp.components_of_type) + ' */')
                continue
            if comp.optional or comp.default_value:
                self.comma()
                self.write('DER_PACK_OPTIONAL')
            if comp.type_decl is not None:
                # TODO: None would be due to components_of_type
                self.generate_pack_node(comp.type_decl, implicit=False)
        if not implicit:
            self.comma()
            self.write('DER_PACK_LEAVE')

    def packSetType(self, node, implicit=False, outer_tag='DER_TAG_SET'):
        if not implicit:
            self.comma()
            self.write('DER_PACK_ENTER | ' + outer_tag)
        for comp in node.components:
            if isinstance(comp, ExtensionMarker):
                # TOOMUCH# self.comma()
                self.write('/* ...ASN.1 extensions... */')
                continue
            if isinstance(comp, ComponentType) and comp.components_of_type is not None:
                # Assuming COMPONENTS OF cannot be OPTIONAL, otherwise move this down
                self.comma()
                self.writeln('DER_PIMP_' + tosym(self.unit) + '_' + tosym(
                    comp.components_of_type.type_name) + '\t/* COMPONENTS OF ' + str(comp.components_of_type) + ' */')
                continue
            if comp.optional or comp.default_value:
                self.comma()
                self.write('DER_PACK_OPTIONAL')
            if comp.type_decl is not None:
                # TODO: None would be due to components_of_type
                self.generate_pack_node(comp.type_decl, implicit=False)
        if not implicit:
            self.comma()
            self.write('DER_PACK_LEAVE')

    def packChoiceType(self, node, implicit=False, outer_tag=None):
        # IMPLICIT tags are invalid for a CHOICE type
        # outer_tags must not be passed down here; will be added
        if implicit or outer_tag is not None:
            self.comma()
            self.write('DER_PACK_ENTER | ' + outer_tag)
        self.comma()
        self.write('DER_PACK_CHOICE_BEGIN')
        for comp in node.components:
            if isinstance(comp, ExtensionMarker):
                # TOOMUCH# self.comma()
                self.write('/* ...ASN.1 extensions... */')
                continue
            if comp.type_decl is not None:
                # TODO: None would be due to components_of_type
                self.generate_pack_node(comp.type_decl, implicit=False)
        self.comma()
        self.write('DER_PACK_CHOICE_END')
        if implicit or outer_tag is not None:
            self.comma()
            self.write('DER_PACK_LEAVE')

    # Sequence Of, Set Of
    def overlayRepeatingStructureType(self, node, tp, fld):
        # Generate a container element for the type...
        self.write('dernode')
        # ...and provoke overlay generation for DER_OVLY_mod_tp_fld
        elem_type = node.type_decl
        if isinstance(elem_type, NamedType):
            # We can ignore node.identifier...
            if fld == '0':
                # ...but in lieu of any name, why not, if it makes rfc4511 cool!
                fld = tosym(elem_type.identifier)
            elem_type = elem_type.type_decl
        # Create future work to describe the repeating elements' type
        self.to_be_overlaid.append((tp + '_' + fld, elem_type))

    # Sequence Of, Set Of
    def psubRepeatingStructureType(self, node, tp, fld, prim):
        elem_type = node.type_decl
        if isinstance(elem_type, NamedType):
            # We can ignore node.identifier...
            if fld == '0':
                # ...but in lieu of any name, why not, if it makes rfc4511 cool!
                fld = tosym(elem_type.identifier)
            elem_type = elem_type.type_decl
        if prim:
            # 1. produce derwalk for the nested field
            dprint('FIRST STEP OF psubRepeatingStructureType()')
            self.comma()
            self.write('const derwalk DER_PACK_' + self.unit + '_' + tp + ('_' + fld if fld else '') + ' [] = {')
            surround_comma = self.getcomma()
            self.newcomma(', \\\n\t\t', ' \\\n\t\t')
            self.generate_pack_node(elem_type, implicit=False)
            self.comma()
            self.write('DER_PACK_END }')
            self.setcomma(*surround_comma)
            # 2. retrieve subquads for the nested field
            dprint('SECOND STEP OF psubRepeatingStructureType()')
            dprint('PROVIDED', tp)
            subquads = self.generate_psub_node(elem_type, tp, fld, False)
            # 3. produce triple structure definition for the nested field
            dprint('THIRD STEP OF psubRepeatingStructureType()')
            self.generate_psub_sub(node, subquads, tp, fld)
        else:
            pass  # TODO:DEBUG# print 'FIRST,SECOND,THIRD STEP OF psubRepeatingStructureType() SKIPPED: SECONDARY'
            # 4. return a fresh triple structure defining this repeating field
            dprint('FOURTH STEP OF psubRepeatingStructureType()')
        nam = self.unit + '_' + tp
        idx = '0'
        esz = 'DER_ELEMSZ (' + self.unit + ',' + tp + ',' + (fld or '') + ')'
        if fld:
            fld = '_' + fld
        else:
            fld = ''
        pck = 'DER_PACK_' + nam + fld
        psb = 'DER_PSUB_' + nam + fld
        return [(idx, esz, pck, psb)]

    def packSequenceOfType(self, node, implicit=False, outer_tag='DER_TAG_SEQUENCE'):
        self.comma()
        self.write('DER_PACK_STORE | ' + outer_tag)

    def packSetOfType(self, node, implicit=False, outer_tag='DER_TAG_SET'):
        self.comma()
        self.write('DER_PACK_STORE | ' + outer_tag)