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
# Copyright (c) 2016 OpenFortress B.V. and InternetWide.org
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

from asn1ate import parser
from asn1ate.sema import * 


def tosym(name):
    """Replace unsupported characters in ASN.1 symbol names"""
    return str(name).replace(' ', '').replace('-', '_')


class QuickDERgen():
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
	self.unit, outext = os.path.splitext (outfn)
        if outext == '.h':
            raise Exception('File cannot overwrite itself -- use another extension than .h for input files')
        self.outfile = open(self.unit + '.h', 'w')
        # Setup function maps
        self.overlay_funmap = {
            DefinedType: self.overlayDefinedType,
            ValueAssignment: self.ignore_node,
            TypeAssignment: self.overlayTypeAssignment,
            TaggedType: self.overlayTaggedType,
            SimpleType: self.overlaySimpleType,
            BitStringType: self.overlaySimpleType,
            ValueListType: self.overlaySimpleType,
            SequenceType: self.overlayConstructedType,
            SetType: self.overlayConstructedType,
            ChoiceType: self.overlayConstructedType,
            SequenceOfType: self.overlaySimpleType,    # var sized
            SetOfType: self.overlaySimpleType,         # var sized
            ComponentType: self.overlaySimpleType,  #TODO#
        }
        self.pack_funmap = {
            DefinedType: self.packDefinedType,
            ValueAssignment: self.ignore_node,
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
            ComponentType: self.packSimpleType,  #TODO#
        }

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

    def close(self):
        self.outfile.close()

    def generate_head(self):
        self.writeln('/*')
        self.writeln(' * asn2quickder output for ' + self.semamod.name + ' -- automatically generated')
        self.writeln(' *')
        self.writeln(' * For information on Quick `n\' Easy DER, see https://github.com/vanrein/quick-der')
        self.writeln(' *')
        self.writeln(' * For information on the code generator, see https://github.com/vanrein/asn2quickder')
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
	rmfns = set ()
        for rm in self.semamod.imports.symbols_imported.keys():
            rmfns.add (tosym(rm.rsplit('.', 1) [0]).lower())
	for rmfn in rmfns:
            self.writeln('#include <quick-der/' + rmfn + '.h>')
            closer = '\n\n'
        self.write(closer)
        closer = ''
        for rm in self.semamod.imports.symbols_imported.keys():
            rmfn = tosym(rm.rsplit('.', 1) [0]).lower()
            for sym in self.semamod.imports.symbols_imported [rm]:
                self.writeln('typedef DER_OVLY_' + tosym(rmfn) + '_' + tosym(sym) + ' DER_OVLY_' + tosym(self.unit) + '_' + tosym(sym) + ';')
                closer = '\n\n'
        self.write(closer)
        closer = ''
        for rm in self.semamod.imports.symbols_imported.keys():
            rmfn = tosym(rm.rsplit('.', 1) [0]).lower()
            for sym in self.semamod.imports.symbols_imported [rm]:
		self.writeln('#define DER_PIMP_' + tosym(self.unit) + '_' + tosym(sym) + '(implicit_tag) DER_PIMP_' + tosym(rmfn) + '_' + tosym(sym) + '(implicit_tag)')
                self.writeln()
                self.writeln('#define DER_PACK_' + tosym(self.unit) + '_' + tosym(sym) + ' DER_PACK_' + tosym(rmfn) + '_' + tosym(sym) + '')
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
                self.generate_overlay_node(assign)

    def generate_pack(self):
        self.writeln()
        self.writeln()
        self.writeln('/* Parser definitions in terms of ASN.1 derived bytecode instructions */')
        self.writeln()
        for assigncompos in dependency_sort(self.semamod.assignments):
            for assign in assigncompos:
                tnm = type(assign)
                if tnm in self.pack_funmap:
                    self.pack_funmap [tnm](assign)
                else:
                    raise Exception('No pack generator for ' + str(tnm))

    def generate_overlay_node(self, node):
        tnm = type(node)
        if tnm in self.overlay_funmap:
            self.overlay_funmap [tnm](node)
        else:
            raise Exception('No overlay generator for ' + str(tnm))

    def generate_pack_node(self, node, **kwargs):
        # kwargs usually captures implicit, outer_tag
        tnm = type(node)
        if tnm in self.pack_funmap:
            self.pack_funmap [tnm](node, **kwargs)
        else:
            raise Exception('No pack generator for ' + str(tnm))

    def ignore_node(self, node):
        pass

    def overlayTypeAssignment(self, node):
        self.write('typedef ')
        self.generate_overlay_node(node.type_decl)
        self.writeln(' DER_OVLY_' + self.unit + '_' + tosym(node.type_name) + ';')
        self.writeln()

    def packTypeAssignment(self, node, implicit=False):
        #TODO# Would be nicer to have DER_PACK_ backref to DER_PIMP_
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

    def overlayDefinedType(self, node):
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

    def overlaySimpleType(self, node):
        self.write('dercursor')

    def packSimpleType(self, node, implicit=False, outer_tag=None):
        if outer_tag is None:
            outer_tag = 'DER_TAG_' + node.type_name.replace(' ', '').upper()
        self.comma()
        self.write('DER_PACK_STORE | ' + outer_tag)

    def overlayTaggedType(self, node):
        # tag = str(node) 
        # tag = tag [:tag.find(']')] + ']'
        # self.write('/* ' + tag + ' */ ')
        # if node.implicity == TagImplicity.IMPLICIT:
        #     tag = tag + ' IMPLICIT'
        # elif node.implicity == TagImplicity.IMPLICIT:
        #     tag = tag + ' EXPLICIT'
        self.generate_overlay_node(node.type_decl)

    def packTaggedType(self, node, implicit=False,outer_tag=None):
        if outer_tag is not None:
           self.comma()
           self.write('DER_PACK_ENTER | ' + outer_tag)
        mytag = 'DER_TAG_' +(node.class_name or 'CONTEXT') + '(' + node.class_number + ')'
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
             self.write('DER_PACK_ENTER | DER_TAG_' +(node.class_name or 'CONTEXT') + '(' + node.class_number + ')')
        implicit_sub = (self.semamod.resolve_tag_implicity(node.implicity, node.type_decl) == TagImplicity.IMPLICIT)
        self.generate_pack_node(node.type_decl, implicit=implicit_sub)
        if not implicit:
            self.comma()
            self.write('DER_PACK_LEAVE')

    # Sequence, Set, Choice
    def overlayConstructedType(self, node, naked=False):
        self.writeln('/* NODE :: ' + str(dir(node)) + ' */')
        if not naked:
            self.writeln('struct {');
        for comp in node.components:
            if isinstance(comp, ExtensionMarker):
                self.writeln('\t/* ...ASN.1 extensions... */')
                continue
            if isinstance(comp, ComponentType) and comp.components_of_type is not None:
                self.writeln('\t/* COMPONENTS OF TYPE ' + str(comp.components_of_type) + ' */')
		self.writeln('//COMP :: ' + str(dir(comp)))
		self.writeln('//TYPE_DECL == ' + str (comp.type_decl))
		self.writeln('//COMPONENTS_OF_TYPE :: ' + str (dir (comp.components_of_type)))
		self.writeln('//CHILDREN :: ' + str (dir (comp.components_of_type.children)))
		self.writeln('//TODO// Not sure how to get to elements and inline them here')
                #TODO:ARG1=???# self.overlayConstructedType (comp.components_of_type, naked=True)
                continue
            self.write('\t')
            self.generate_overlay_node(comp.type_decl)
            self.writeln(' ' + tosym(comp.identifier) + '; // ' + str(comp.type_decl))
        if not naked:
            self.write('}')

    def packSequenceType(self, node, implicit=False, outer_tag='DER_TAG_SEQUENCE'):
        if not implicit:
            self.comma()
            self.write('DER_PACK_ENTER | ' + outer_tag)
        for comp in node.components:
            if isinstance(comp, ExtensionMarker):
                #TOOMUCH# self.comma()
                self.write('/* ...ASN.1 extensions... */')
                continue
            if isinstance(comp, ComponentType) and comp.components_of_type is not None:
                # Assuming COMPONENTS OF cannot be OPTIONAL, otherwise move this down
                self.comma()
                self.writeln('DER_PIMP_' + tosym(self.unit) + '_' + tosym(comp.components_of_type.type_name) + '\t/* COMPONENTS OF ' + str(comp.components_of_type) + ' */')
                continue
            if comp.optional:
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
                #TOOMUCH# self.comma()
                self.write('/* ...ASN.1 extensions... */')
                continue
            if isinstance(comp, ComponentType) and comp.components_of_type is not None:
                # Assuming COMPONENTS OF cannot be OPTIONAL, otherwise move this down
                self.comma()
                self.writeln('DER_PIMP_' + tosym(self.unit) + '_' + tosym(comp.components_of_type.type_name) + '\t/* COMPONENTS OF ' + str(comp.components_of_type) + ' */')
                continue
            if comp.optional:
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
                #TOOMUCH# self.comma()
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

    def packSequenceOfType(self, node, implicit=False, outer_tag='DER_TAG_SEQUENCE'):
        self.comma()
        self.write('DER_PACK_STORE | ' + outer_tag)

    def packSetOfType(self, node, implicit=False, outer_tag='DER_TAG_SET'):
        self.comma()
        self.write('DER_PACK_STORE | ' + outer_tag)


"""The main program asn2quickder is called with one or more .asn1 files,
   the first of which is mapped to a C header file and the rest is
   loaded to fulfil dependencies.
"""

if len(sys.argv) < 2:
    sys.stderr.write('Usage: %s main[.asn1] dependency[.asn1]...\n'
        % sys.argv [0])
    sys.exit(1)

mods = []
for file in sys.argv [1:]:
    print('Parsing', file)
    with open(file, 'r') as asn1fh:
        asn1txt  = asn1fh.read()
        asn1tree = parser.parse_asn1(asn1txt)
    print('Building semantic model for', file)
    asn1sem = build_semantic_model(asn1tree)
    mods.insert(0, asn1sem [0])
    print('Realised semantic model for', file)

cogen = QuickDERgen(mods [-1], os.path.basename(sys.argv [1]), mods [1:])

cogen.generate_head()
cogen.generate_overlay()
cogen.generate_pack()
cogen.generate_tail()

cogen.close()
