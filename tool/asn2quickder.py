#!/usr/bin/env python
#
# asn2quickder -- Generate header files for C for use with Quick `n' Easy DER
#
# This program owes a lot to asn1ate, which was built to generate pyasn1
# classes, but which was so well-written that it could be extended with a
# code generator for Quick DER.
#
# Much of the code below is diagonally inspired on the pyasn1 backend, so
# a very big thank you to Schneider Electric Buildings AB for helping to
# make this program possible!
#
# Copyright (c) 2016-2017 OpenFortress B.V. and InternetWide.org
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Schneider Electric Buildings AB nor the
#       names of contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#


import sys
import os.path
import getopt
import re

from asn1ate import parser
from asn1ate.sema import *

# from quick_der import api
import quick_der.packstx as api


def tosym(name):
    """Replace unsupported characters in ASN.1 symbol names"""
    return str(name).replace(' ', '').replace('-', '_')


api_prefix = '_api'

dertag2atomsubclass = {
    api.DER_TAG_BOOLEAN: 'ASN1Boolean',
    api.DER_TAG_INTEGER: 'ASN1Integer',
    api.DER_TAG_BITSTRING: 'ASN1BitString',
    api.DER_TAG_OCTETSTRING: 'ASN1OctetString',
    api.DER_TAG_NULL: 'ASN1Null',
    api.DER_TAG_OID: 'ASN1OID',
    api.DER_TAG_REAL: 'ASN1Real',
    api.DER_TAG_ENUMERATED: 'ASN1Enumerated',
    api.DER_TAG_UTF8STRING: 'ASN1UTF8String',
    api.DER_TAG_RELATIVEOID: 'ASN1RelativeOID',
    api.DER_TAG_NUMERICSTRING: 'ASN1NumericString',
    api.DER_TAG_PRINTABLESTRING: 'ASN1PrintableString',
    api.DER_TAG_TELETEXSTRING: 'ASN1TeletexString',
    api.DER_TAG_VIDEOTEXSTRING: 'ASN1VideoTexString',
    api.DER_TAG_IA5STRING: 'ASN1IA5String',
    api.DER_TAG_UTCTIME: 'ASN1UTCTime',
    api.DER_TAG_GENERALIZEDTIME: 'ASN1GeneralizedTime',
    api.DER_TAG_GRAPHICSTRING: 'ASN1GraphicString',
    api.DER_TAG_VISIBLESTRING: 'ASN1VisibleString',
    api.DER_TAG_GENERALSTRING: 'ASN1GeneralString',
    api.DER_TAG_UNIVERSALSTRING: 'ASN1UniversalString',
    api.DER_PACK_ANY: 'ASN1Any'
}


class QuickDERgeneric(object):
    def __init__(self, outfn, outext):
        self.unit, curext = os.path.splitext(outfn)
        if curext == '.h':
            raise Exception('File cannot overwrite itself -- use another extension than ' + outext + ' for input files')
        self.outfile = open(self.unit + outext, 'w')

    def write(self, txt):
        self.outfile.write(txt)

    def writeln(self, txt=''):
        self.outfile.write(txt + '\n')

    def newcomma(self, comma, firstcomma=''):
        self.comma0 = firstcomma
        self.comma1 = comma

    def comma(self):
        self.write(self.comma0)
        self.comma0 = self.comma1

    def getcomma(self):
        return (self.comma1, self.comma0)

    def setcomma(self, comma1, comma0):
        self.comma1 = comma1
        self.comma0 = comma0

    def close(self):
        self.outfile.close()


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
        for rm in self.semamod.imports.symbols_imported.keys():
            rmfns.add(tosym(rm.rsplit('.', 1)[0]).lower())
        for rmfn in rmfns:
            self.writeln('#include <quick-der/' + rmfn + '.h>')
            closer = '\n\n'
        self.write(closer)
        closer = ''
        for rm in self.semamod.imports.symbols_imported.keys():
            rmfn = tosym(rm.rsplit('.', 1)[0]).lower()
            for sym in self.semamod.imports.symbols_imported[rm]:
                self.writeln('typedef DER_OVLY_' + tosym(rmfn) + '_' + tosym(sym) + ' DER_OVLY_' + tosym(
                    self.unit) + '_' + tosym(sym) + ';')
                closer = '\n\n'
        self.write(closer)
        closer = ''
        for rm in self.semamod.imports.symbols_imported.keys():
            rmfn = tosym(rm.rsplit('.', 1)[0]).lower()
            for sym in self.semamod.imports.symbols_imported[rm]:
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
                    # TODO:DEBUG# print 'Recursive call for', tnm
                    self.psub_funmap[tnm](assign, None, None, True)
                    # TODO:DEBUG# print 'Recursion done for', tnm
                else:
                    raise Exception('No psub generator for ' + str(tnm))

    def generate_psub_sub(self, node, subquads, tp, fld):
        if fld is None:
            fld = ''
        else:
            fld = '_' + fld
        # OLD:TEST:TODO# mod = node.module_name or self.unit
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
        # TODO:DEBUG# print 'generate_psub_node() CALLED ON', tnm
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
            if not self.issued_typedefs.has_key(key):
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
        # TODO:DEBUG# print 'SUBTRIPLES =', subquads
        if subquads != []:
            self.generate_psub_sub(node.type_decl, subquads, tp, None)
            self.write(';\n\n')
        return []

    def overlayDefinedType(self, node, tp, fld):
        mod = node.module_name or self.unit
        self.write('DER_OVLY_' + tosym(mod) + '_' + tosym(node.type_name))

    def packDefinedType(self, node, implicit=False, outer_tag=None):
        # There should never be anything of interest in outer_tag
        mod = node.module_name or self.unit
        self.comma()
        if outer_tag is None:
            tagging = 'DER_PACK_'
            param = ''
        else:
            tagging = 'DER_PIMP_'
            param = '(' + outer_tag + ')'
        self.write(tagging + tosym(mod) + '_' + tosym(node.type_name) + param)

    def psubDefinedType(self, node, tp, fld, prim):
        # TODO:DEBUG# print 'DefinedType type:', node.type_name, '::', type (node.type_name)
        modnm = node.module_name
        # TODO:DEBUG# print 'AFTER modnm = node.module_name', modnm
        if modnm is None:
            syms = self.semamod.imports.symbols_imported
            # TODO:DEBUG# print 'SYMS.KEYS() =', syms.keys ()
            for mod in syms.keys():
                if node.type_name in syms[mod]:
                    modnm = mod.lower()
                    # TODO:DEBUG# print 'AFTER modnm = mod.lower ()', modnm
                    break
        if modnm is None:
            # NOT_IN_GENERAL# modnm = node.module_name
            modnm = self.unit.lower()
            # TODO:DEBUG# print 'AFTER modnm = self.unit.lower ()', modnm
            # TODO:DEBUG# print 'MODNM =', modnm, '::', type (modnm)
            # TODO:DEBUG# print 'Referenced module:', modnm, '::', type (modnm)
            # TODO:DEBUG# print 'Searching case-insensitively in:', self.refmods.keys ()
        if not self.refmods.has_key(modnm):
            raise Exception('Module name "%s" not found' % modnm)
        thetype = self.refmods[modnm].user_types()[node.type_name]
        # TODO:DEBUG# print 'References:', thetype, '::', type (thetype)
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
        # TODO:DEBUG# print 'SUBTUPLES =', subtuples
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
        if self.semamod.resolve_tag_implicity(node.implicity, node.type_decl) == TagImplicity.IMPLICIT:
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
        implicit_sub = (self.semamod.resolve_tag_implicity(node.implicity, node.type_decl) == TagImplicity.IMPLICIT)
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
            self.writeln('struct DER_OVLY_' + self.unit + '_' + tp + fld + ' {');
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
            subfld = tosym(comp.identifier);
            self.generate_overlay_node(comp.type_decl, tp, subfld)
            self.writeln(' ' + subfld + '; // ' + str(comp.type_decl))
        if not naked:
            self.write('}')

    # Sequence, Set, Choice
    def psubConstructedType(self, node, tp, fld, prim):
        # Iterate over field names, recursively retrieving quads;
        # add the field's offset to each of the quads, for its holding field
        # TODO:DEBUG# print 'OVERLAY =', ovly
        compquads = []
        for comp in node.components:
            if isinstance(comp, ExtensionMarker):
                continue
            subfld = tosym(comp.identifier)
            # TODO:DEBUG# print ('subfld is ' + subfld)
            # TODO:DEBUG# print ('Generating PSUB node for ' + str (comp.type_decl.type_name))
            subquads = self.generate_psub_node(comp.type_decl, tp, subfld, prim)
            # TODO:DEBUG# print ('Generated  PSUB node for ' + str (comp.type_decl.type_name))
            # TODO:DEBUG# print ('quads are ' + str (subquads))
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
                # TODO:DEBUG# print 'DEALING WITH', pck
                if str(idx) == '0':
                    idx = ofs
                else:
                    idx = ofs + ' \\\n\t\t+ ' + str(idx)
                compquads.append((idx, esz, pck, psb))
        # TODO:DEBUG# print 'psubConstructedType() RETURNS COMPONENT TRIPLES', compquads
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
            # TODO:DEBUG# print 'FIRST STEP OF psubRepeatingStructureType()'
            self.comma()
            self.write('const derwalk DER_PACK_' + self.unit + '_' + tp + ('_' + fld if fld else '') + ' [] = {')
            surround_comma = self.getcomma()
            self.newcomma(', \\\n\t\t', ' \\\n\t\t')
            self.generate_pack_node(elem_type, implicit=False)
            self.comma()
            self.write('DER_PACK_END }')
            self.setcomma(*surround_comma)
            # 2. retrieve subquads for the nested field
            # TODO:DEBUG# print 'SECOND STEP OF psubRepeatingStructureType()'
            # TODO:DEBUG# print 'PROVIDED', tp
            subquads = self.generate_psub_node(elem_type, tp, fld, False)
            # 3. produce triple structure definition for the nested field
            # TODO:DEBUG# print 'THIRD STEP OF psubRepeatingStructureType()'
            self.generate_psub_sub(node, subquads, tp, fld)
        else:
            pass  # TODO:DEBUG# print 'FIRST,SECOND,THIRD STEP OF psubRepeatingStructureType() SKIPPED: SECONDARY'
            # 4. return a fresh triple structure defining this repeating field
            # TODO:DEBUG# print 'FOURTH STEP OF psubRepeatingStructureType()'
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


class QuickDER2py(QuickDERgeneric):
    """Generate Python modules with Quick DER definitions, based on
       generic definitions in the quick_der module.  The main task of
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
        self.writeln('import quick_der.api as ' + api_prefix)
        self.writeln()
        imports = self.semamod.imports.symbols_imported
        for rm in imports.keys():
            pymod = tosym(rm.rsplit('.', 1)[0]).lower()
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
                (_NAMED, map) = recp
                ln += '    '
                retval = "('_NAMED', {"
                comma = False
                for (fld, fldrcp) in map.items():
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
                retval = repr(recp)
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
        if type(recp) == int:
            dertag = eval(pck[0], api.__dict__)
            if dertag2atomsubclass.has_key(dertag):
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
            assert Fail, 'Unknown recipe tag ' + str(recp[0])
        numcrs = self.cursor_offset
        pygen_class(tosym(node.type_name), tp, ofs, pck, recp, numcrs)

    def generate_pytype(self, node, **subarg):
        # DEBUG# sys.stderr.write ('Node = ' + str (node) + '\n')
        tnm = type(node)
        if tnm not in self.funmap_pytype.keys():
            raise Exception('Failure to generate a python type for ' + str(tnm))
        return self.funmap_pytype[tnm](node, **subarg)

    def pytypeDefinedType(self, node, **subarg):
        modnm = node.module_name
        if modnm is None:
            syms = self.semamod.imports.symbols_imported
            for mod in syms.keys():
                if node.type_name in syms[mod]:
                    modnm = mod.lower()
                    break
        if modnm is None:
            modnm = self.unit.lower()
        if not self.refmods.has_key(modnm):
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
        return (pck, recp)

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
        if dertag2atomsubclass.has_key(simptag):
            recp = ('_TYPTR', [api_prefix + '.' + dertag2atomsubclass[simptag]], recp)
        return (pck, recp)

    def pytypeTagged(self, node, implicit_tag=None):
        mytag = 'DER_TAG_' + (node.class_name or 'CONTEXT') + '(' + node.class_number + ')'
        if self.semamod.resolve_tag_implicity(node.implicity, node.type_decl) == TagImplicity.IMPLICIT:
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
        return (pck, recp)

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
        return (pck, ('_NAMED', recp))

    def pytypeChoice(self, node, implicit_tag=None):
        (pck, recp) = self.pyhelpConstructedType(node)
        pck = ['DER_PACK_CHOICE_BEGIN'] + pck + ['DER_PACK_CHOICE_END']
        if implicit_tag:
            # Can't have an implicit tag around a CHOICE
            pck = ['DER_PACK_ENTER | ' + implicit_tag] + pck + ['DER_PACK_LEAVE']
        return (pck, recp)

    def pytypeSequence(self, node, implicit_tag='DER_TAG_SEQUENCE'):
        (pck, recp) = self.pyhelpConstructedType(node)
        pck = ['DER_PACK_ENTER | ' + implicit_tag] + pck + ['DER_PACK_LEAVE']
        return (pck, recp)

    def pytypeSet(self, node, implicit_tag='DER_TAG_SET'):
        (pck, recp) = self.pyhelpConstructedType(node)
        pck = ['DER_PACK_ENTER | ' + implicit_tag] + pck + ['DER_PACK_LEAVE']
        return (pck, recp)

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
        return (pck, (recptag, allidx, subpck, subnum, subrcp))

    def pytypeSequenceOf(self, node, implicit_tag='DER_TAG_SEQUENCE'):
        return self.pyhelpRepeatedType(node, implicit_tag, '_SEQOF')

    def pytypeSetOf(self, node, implicit_tag='DER_TAG_SET'):
        return self.pyhelpRepeatedType(node, implicit_tag, '_SETOF')


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
        (max, fun) = self.type2tdgen[typename]
        if casenr >= max:
            return None
        assert casenr < max, 'Case number out of range for ' + typename
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
        modnm = node.module_name
        if modnm is None:
            syms = self.semamod.imports.symbols_imported
            for mod in syms.keys():
                if node.type_name in syms[mod]:
                    modnm = mod.lower()
                    break
        if modnm is None:
            modnm = self.unit.lower()
        if not self.refmods.has_key(modnm):
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

        return (len(cases), do_gen)

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
        am_implicit = self.semamod.resolve_tag_implicity(node.implicity, node.type_decl) == TagImplicity.IMPLICIT
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

        return (subcnt, do_gen)

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
            round = 0
            # Invariants for the following loop:
            #  - We have made "round" passes over all components
            #  - Considering that some components end before others
            #  - We still have to generate "casenr" new values
            #  - Skips for "round" are in "elcnts_sorted[round]"
            while casenr >= round2flips[round]:
                casenr -= round2flips[round]
                round += 1
            eltidx = 0
            # Invariants for the following loop:
            #  - We have made "round" passes over all components
            #  - Considering that some components end before others
            #  - We still have to generate "casenr" new values
            #  - The current "round" contains new "casenr" value
            #  - Searching for "eltidx" for the value to generate
            while True:
                if elcnts[eltidx] > round:
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
            retval = elgens[eltidx](round)
            if implicit_tag is not None:
                retval = self.der_prefixhead(implicit_tag, retval)
            return retval

        return (totcnt, do_gen)

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
            round = 0
            # Invariants for the following loop:
            #  - We have made "round" passes over all components
            #  - Considering that some components end before others
            #  - We still have to generate "casenr" new values
            #  - Skips for "round" are in "elcnts_sorted[round]"
            while casenr >= round2flips[round]:
                casenr -= round2flips[round]
                round += 1
            eltidx = 0
            # Invariants for the following loop:
            #  - We have made "round" passes over all components
            #  - Considering that some components end before others
            #  - We still have to generate "casenr" new values
            #  - The current "round" contains new "casenr" value
            #  - Searching for "eltidx" for the value to generate
            while True:
                if elcnts[eltidx] > round:
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
            if round > 0:
                retval += elgens[eltidx](round)
                eltidx += 1
            retval += comp[eltidx:]
            retval = ''.join(retval)
            retval = self.der_prefixhead(tag, retval)
            return retval

        return (totcnt, do_gen)

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

        return (totcnt, do_gen)


"""The main program asn2quickder is called with one or more .asn1 files,
   the first of which is mapped to a C header file and the rest is
   loaded to fulfil dependencies.
"""

if len(sys.argv) < 2:
    sys.stderr.write('Usage: %s [-I incdir] [-l proglang] [-t testcases] ... main.asn1 [dependency.asn1] ...\n'
                     % sys.argv[0])
    sys.exit(1)

# Test case notation: [asn1id=] [[ddd]-]ddd ...
casesyntax = re.compile('^(?:([A-Z][A-Za-z0-9-]*)=)?((?:([0-9]*-)?[0-9]+)(?:,(?:[0-9]*-)?[0-9]+)*)$')
cases2find = re.compile('(?:([0-9]*)(-))?([0-9]+)')

defmods = {}
refmods = {}
incdirs = []
langopt = ['c', 'python']
langsel = set()
testcases = {}
(opts, restargs) = getopt.getopt(sys.argv[1:], 'I:l:t:', longopts=langopt)
for (opt, optarg) in opts:
    if opt == '-I':
        incdirs.append(optarg)
    elif opt == '-l':
        if optarg not in langopt:
            sys.stderr.write(
                'No code generator backend for ' + optarg + '\nAvailable backends: ' + ', '.join(langopt) + '\n')
            sys.exit(1)
        langsel.add(optarg)
    elif opt == '-t':
        m = casesyntax.match(optarg)
        if m is None:
            sys.stderr.write('Wrong syntax for -t [asn1id=][[ddd]-]ddd,...\n')
            sys.exit(1)
        asn1id = m.group(1) or ''
        series = m.group(2)
        for (start, dash, end) in cases2find.findall(series):
            end = int(end)
            if len(start) > 0:
                start = int(start)
            elif len(dash) == 0:
                start = end
            else:
                start = 0
            if not testcases.has_key(asn1id):
                testcases[asn1id] = []
            testcases[asn1id].append((start, end))
    elif optarg[:2] == '--' and optarg[2:] in langopts:
        langsel.add(optarg)
    else:
        sys.stderr.write(
            'Usage: ' + sys.argv[0] + ' [-I incdir] [-l proglang] [-t testcases] ... main.asn1 [dependency.asn1] ...\n')
        sys.exit(1)
if len(langsel) == 0:
    langsel = set(langopt)
incdirs.append(os.path.curdir)
for file in restargs:
    modnm = os.path.basename(file).lower()
    # TODO:DEBUG# print('Parsing ASN.1 syntaxdef for "%s"' % modnm)
    with open(file, 'r') as asn1fh:
        asn1txt = asn1fh.read()
        asn1tree = parser.parse_asn1(asn1txt)
    # TODO:DEBUG# print('Building semantic model for "%s"' % modnm)
    asn1sem = build_semantic_model(asn1tree)
    defmods[os.path.basename(file)] = asn1sem[0]
    refmods[os.path.splitext(modnm)[0]] = asn1sem[0]
    # TODO:DEBUG# print('Realised semantic model for "%s"' % modnm)

imports = refmods.keys()
while len(imports) > 0:
    dm = refmods[imports.pop(0).lower()]
    for rm in dm.imports.symbols_imported.keys():
        rm = rm.lower()
        if not refmods.has_key(rm):
            # TODO:DEBUG# print ('Importing ASN.1 include for "%s"' % rm)
            modfh = None
            for incdir in incdirs:
                try:
                    modfh = open(incdir + os.path.sep + rm + '.asn1', 'r')
                    break
                except IOError:
                    continue
            if modfh is None:
                raise Exception('No include file "%s.asn1" found' % rm)
            asn1txt = modfh.read()
            asn1tree = parser.parse_asn1(asn1txt)
            # TODO:DEBUG# print ('Building semantic model for "%s"' % rm)
            asn1sem = build_semantic_model(asn1tree)
            refmods[rm] = asn1sem[0]
            imports.append(rm)
            # TODO:DEBUG# print('Realised semantic model for "%s"' % rm)

# Generate C header files
if 'c' in langsel:
    for modnm in defmods.keys():
        # TODO:DEBUG# print ('Generating C header file for "%s"' % modnm)
        cogen = QuickDER2c(defmods[modnm], modnm, refmods)
        cogen.generate_head()
        cogen.generate_overlay()
        cogen.generate_pack()
        cogen.generate_psub()
        cogen.generate_tail()
        cogen.close()
        # TODO:DEBUG# print ('Ready with C header file for "%s"' % modnm)

# Generate Python modules
if 'python' in langsel:
    for modnm in defmods.keys():
        # TODO:DEBUG# print ('Generating Python module for "%s"' % modnm)
        cogen = QuickDER2py(defmods[modnm], modnm, refmods)
        cogen.generate_head()
        cogen.generate_classes()
        cogen.generate_values()
        cogen.generate_tail()
        cogen.close()
        # TODO:DEBUG# print ('Ready with Python module for "%s"' % modnm)

# Generate test data
if testcases != {}:
    for modnm in defmods.keys():
        print ('Generating test cases for ' + modnm)
        cogen = QuickDER2testdata(defmods[modnm], modnm, refmods)
        cogen.generate_testdata()
        for typenm in cogen.all_typenames():
            if testcases.has_key(typenm):
                cases = testcases[typenm]
            elif testcases.has_key(''):
                cases = testcases['']
            else:
                cases = []
            casestr = ','.join([str(s) + '-' + str(e) for (s,e) in cases])
            for (casenr, der_packer) in cogen.fetch_multi(typenm, cases):
                if der_packer is None:
                    break
                print 'Type', typenm, 'case', casenr, 'packer', der_packer.encode('hex')
        cogen.close()
        print ('Generated  test cases for ' + modnm)
