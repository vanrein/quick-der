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

from asn1ate import parser
from asn1ate.sema import * 


def tosym(name):
    """Replace unsupported characters in ASN.1 symbol names"""
    return str(name).replace(' ', '').replace('-', '_')


class QuickDERgeneric (object):

    def __init__ (self, outfn, outext):
        self.unit, curext = os.path.splitext (outfn)
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

    def setcomma(self, (comma1,comma0)):
        self.comma1 = comma1
        self.comma0 = comma0

    def close(self):
        self.outfile.close()


class QuickDER2c (QuickDERgeneric):
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
	super (QuickDER2c,self).__init__ (outfn, '.h')
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
            ComponentType: self.overlaySimpleType,  #TODO#
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
            ComponentType: self.packSimpleType,  #TODO#
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
            ComponentType: self.psubSimpleType,  #TODO#
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
                    self.pack_funmap [tnm](assign)
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
		    #TODO:DEBUG# print 'Recursive call for', tnm
                    self.psub_funmap [tnm](assign, None, None, True)
		    #TODO:DEBUG# print 'Recursion done for', tnm
                else:
                    raise Exception('No psub generator for ' + str(tnm))

    def generate_psub_sub(self, node, subquads, tp, fld):
        if fld is None:
            fld = ''
        else:
            fld = '_' + fld
        #OLD:TEST:TODO# mod = node.module_name or self.unit
        mod = self.unit
        self.comma ()
        self.writeln ('const struct der_subparser_action DER_PSUB_' + mod + '_' + tp + fld + ' [] = { \\')
        for (idx,esz,pck,sub) in subquads:
            self.writeln ('\t\t{ ' + str (idx) + ', \\')
	    self.writeln ('\t\t  ' + str (esz) + ', \\')
            self.writeln ('\t\t  ' + pck + ', \\')
            self.writeln ('\t\t  ' + sub + ' }, \\')
        self.writeln ('\t\t{ 0, 0, NULL, NULL } \\')
        self.write ('\t}')

    def generate_overlay_node(self, node, tp, fld):
        tnm = type(node)
        if tnm in self.overlay_funmap:
            self.overlay_funmap [tnm](node, tp, fld)
        else:
            raise Exception('No overlay generator for ' + str(tnm))

    def generate_pack_node(self, node, **kwargs):
        # kwargs usually captures implicit, outer_tag
        tnm = type(node)
        if tnm in self.pack_funmap:
            self.pack_funmap [tnm](node, **kwargs)
        else:
            raise Exception('No pack generator for ' + str(tnm))

    def generate_psub_node(self, node, tp, fld, prim):
        tnm = type(node)
	#TODO:DEBUG# print 'generate_psub_node() CALLED ON', tnm
        if tnm in self.psub_funmap:
            return self.psub_funmap [tnm](node, tp, fld, prim)
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
	self.to_be_overlaid = [ (tosym (node.type_name),node.type_decl) ]
	while len (self.to_be_overlaid) > 0:
	    (tname,tdecl) = self.to_be_overlaid.pop (0)
            key = (self.unit, tname)
            if not self.issued_typedefs.has_key (key):
                self.issued_typedefs [key] = str (tdecl)
                self.write('typedef ')
                self.generate_overlay_node (tdecl, tname, '0')
                self.writeln(' DER_OVLY_' + self.unit + '_' + tname + ';')
                self.writeln()
            else:
                if self.issued_typedefs [key] != str (tdecl):
                    raise TypeError("Redefinition of type %s." % key[1])
	for tbd in self.to_be_defined:
		if tbd != 'DER_OVLY_' + self.unit + '_' + tosym (node.type_name) + '_0':
			self.writeln ('typedef struct ' + tbd + ' ' + tbd + ';')
	self.writeln ()

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

    def psubTypeAssignment(self, node, tp, fld, prim):
        # In lieu of typing context, fld is None; tp probably is too
	self.newcomma ('; \\\n\t', '#define DEFINE_DER_PSUB_' + self.unit + '_' + tosym (node.type_name) + ' \\\n\t')
	tp = tosym (node.type_name)
	subquads = self.generate_psub_node (node.type_decl, tp, '0', prim)
	#TODO:DEBUG# print 'SUBTRIPLES =', subquads
	if subquads != []:
		self.generate_psub_sub (node.type_decl, subquads, tp, None)
		self.write (';\n\n')
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
	#TODO:DEBUG# print 'DefinedType type:', node.type_name, '::', type (node.type_name)
	modnm = node.module_name
	#TODO:DEBUG# print 'AFTER modnm = node.module_name', modnm
	if modnm is None:
	    syms = self.semamod.imports.symbols_imported
	    #TODO:DEBUG# print 'SYMS.KEYS() =', syms.keys ()
	    for mod in syms.keys ():
		if node.type_name in syms [mod]:
		    modnm = mod.lower ()
		    #TODO:DEBUG# print 'AFTER modnm = mod.lower ()', modnm
		    break
	if modnm is None:
	    #NOT_IN_GENERAL# modnm = node.module_name
	    modnm = self.unit.lower ()
	    #TODO:DEBUG# print 'AFTER modnm = self.unit.lower ()', modnm
	    #TODO:DEBUG# print 'MODNM =', modnm, '::', type (modnm)
	#TODO:DEBUG# print 'Referenced module:', modnm, '::', type (modnm)
	#TODO:DEBUG# print 'Searching case-insensitively in:', self.refmods.keys ()
	if not self.refmods.has_key (modnm):
	    raise Exception ('Module name "%s" not found' % modnm)
	thetype = self.refmods [modnm].user_types () [node.type_name]
	#TODO:DEBUG# print 'References:', thetype, '::', type (thetype)
	popunit = self.unit
	popsema = self.semamod
	self.unit = modnm
	self.semamod = self.refmods [modnm]
	tp2 = tosym (node.type_name)
	fld2 = '0'
        subtuples = self.generate_psub_node (thetype, tp2, fld2,
			prim and (popunit == self.unit) and (tp == tp2))
	self.semamod = popsema
	self.unit = popunit
	#TODO:DEBUG# print 'SUBTUPLES =', subtuples
	return subtuples

    def overlaySimpleType(self, node, tp, fld):
        self.write('dercursor')

    def packSimpleType(self, node, implicit=False, outer_tag=None):
        if outer_tag is None:
            simptp = node.type_name.replace(' ', '').upper()
            if simptp == 'ANY':
                # exceptional syntax, just the instruction DER_PACK_ANY
                self.comma ()
                self.write ('DER_PACK_ANY')
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
                self.to_be_defined.append ('DER_OVLY_' + self.unit + '_' + tp + fld)
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
	    subfld = tosym (comp.identifier);
            self.generate_overlay_node(comp.type_decl, tp, subfld)
            self.writeln(' ' + subfld + '; // ' + str(comp.type_decl))
        if not naked:
            self.write('}')

    # Sequence, Set, Choice
    def psubConstructedType(self, node, tp, fld, prim):
        # Iterate over field names, recursively retrieving quads;
        # add the field's offset to each of the quads, for its holding field
	#TODO:DEBUG# print 'OVERLAY =', ovly
        compquads = []
        for comp in node.components:
	    if isinstance (comp, ExtensionMarker):
		continue
            subfld = tosym (comp.identifier)
	    #TODO:DEBUG# print ('subfld is ' + subfld)
	    #TODO:DEBUG# print ('Generating PSUB node for ' + str (comp.type_decl.type_name))
            subquads = self.generate_psub_node (comp.type_decl, tp, subfld, prim)
	    #TODO:DEBUG# print ('Generated  PSUB node for ' + str (comp.type_decl.type_name))
	    #TODO:DEBUG# print ('quads are ' + str (subquads))
            if fld == '0':
                subtp = tp
            else:
                subtp = tp + '_' + fld
            #TODO:TEST# subtp = tp + ('_' + fld if fld else '')
            #TODO:TEST# if subfld != '0':
	    #TODO:TEST# if subfld:
            if subfld != '0':
		ofs = 'DER_OFFSET (' + self.unit + ',' + subtp + ',' + subfld + ')'
	    else:
		ofs = '0'
            for (idx,esz,pck,psb) in subquads:
		#TODO:DEBUG# print 'DEALING WITH', pck
                if str (idx) == '0':
                    idx = ofs
                else:
                    idx = ofs + ' \\\n\t\t+ ' + str (idx)
                compquads.append ( (idx,esz,pck,psb) )
	#TODO:DEBUG# print 'psubConstructedType() RETURNS COMPONENT TRIPLES', compquads
        return compquads

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

    # Sequence Of, Set Of
    def overlayRepeatingStructureType(self, node, tp, fld):
	# Generate a container element for the type...
        self.write('dernode')
	# ...and provoke overlay generation for DER_OVLY_mod_tp_fld
	elem_type = node.type_decl
        if isinstance (elem_type, NamedType):
            # We can ignore node.identifier...
            if fld == '0':
                # ...but in lieu of any name, why not, if it makes rfc4511 cool!
		fld = tosym (elem_type.identifier)
            elem_type = elem_type.type_decl
	# Create future work to describe the repeating elements' type
	self.to_be_overlaid.append ( (tp+'_'+fld,elem_type) )

    # Sequence Of, Set Of
    def psubRepeatingStructureType(self, node, tp, fld, prim):
	elem_type = node.type_decl
        if isinstance (elem_type, NamedType):
            # We can ignore node.identifier...
            if fld == '0':
                # ...but in lieu of any name, why not, if it makes rfc4511 cool!
		fld = tosym (elem_type.identifier)
            elem_type = elem_type.type_decl
	if prim:
            # 1. produce derwalk for the nested field
	    #TODO:DEBUG# print 'FIRST STEP OF psubRepeatingStructureType()'
            self.comma ()
            self.write ('const derwalk DER_PACK_' + self.unit + '_' + tp + ('_' + fld if fld else '') + ' [] = {')
            surround_comma = self.getcomma ()
            self.newcomma (', \\\n\t\t', ' \\\n\t\t')
            self.generate_pack_node (elem_type, implicit=False)
	    self.comma ()
            self.write ('DER_PACK_END }')
            self.setcomma (surround_comma)
            # 2. retrieve subquads for the nested field
	    #TODO:DEBUG# print 'SECOND STEP OF psubRepeatingStructureType()'
	    #TODO:DEBUG# print 'PROVIDED', tp
            subquads = self.generate_psub_node (elem_type, tp, fld, False)
            # 3. produce triple structure definition for the nested field
	    #TODO:DEBUG# print 'THIRD STEP OF psubRepeatingStructureType()'
            self.generate_psub_sub (node, subquads, tp, fld)
	else:
	    pass #TODO:DEBUG# print 'FIRST,SECOND,THIRD STEP OF psubRepeatingStructureType() SKIPPED: SECONDARY'
        # 4. return a fresh triple structure defining this repeating field
	#TODO:DEBUG# print 'FOURTH STEP OF psubRepeatingStructureType()'
        nam = self.unit + '_' + tp
	idx = '0'
	esz = 'DER_ELEMSZ (' + self.unit + ',' + tp + ',' + (fld or '') + ')'
	if fld:
		fld = '_' + fld
	else:
		fld = ''
        pck = 'DER_PACK_' + nam + fld
        psb = 'DER_PSUB_' + nam + fld
        return [ (idx,esz,pck,psb) ]

    def packSequenceOfType(self, node, implicit=False, outer_tag='DER_TAG_SEQUENCE'):
        self.comma()
        self.write('DER_PACK_STORE | ' + outer_tag)

    def packSetOfType(self, node, implicit=False, outer_tag='DER_TAG_SET'):
        self.comma()
        self.write('DER_PACK_STORE | ' + outer_tag)


class QuickDER2py (QuickDERgeneric):
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
		super (QuickDER2py,self).__init__ (outfn, '.py')
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

	def comment (self, text):
		for ln in str (text).split ('\n'):
			self.writeln ('# ' + ln)

	def generate_head (self):
		self.writeln ('#')
		self.writeln ('# asn2quickder output for ' + self.semamod.name + ' -- automatically generated')
		self.writeln ('#')
		self.writeln ('# Read more about Quick `n\' Easy DER on https://github.com/vanrein/quick-der')
		self.writeln ('#')
		self.writeln ()
		self.writeln ()
		self.writeln ('#')
		self.writeln ('# Import general definitions and package dependencies')
		self.writeln ('#')
		self.writeln ()
		self.writeln ('import quick_der.api as _api')
		self.writeln ()
		imports = self.semamod.imports.symbols_imported
		for rm in imports.keys ():
			pymod = tosym(rm.rsplit('.', 1) [0]).lower()
			self.write ('from ' + pymod + ' import ')
			self.writeln (', '.join (map (tosym, imports [rm])))
		self.writeln ()
		self.writeln ()

	def generate_tail (self):
		self.writeln()
		self.writeln('# asn2quickder output for ' + self.semamod.name + ' ends here')

	def generate_values (self):
		self.writeln ('#')
		self.writeln ('# Variables with ASN.1 value assignments')
		self.writeln ('#')
		self.writeln ()
		for assigncompos in dependency_sort(self.semamod.assignments):
			for assign in assigncompos:
				if type (assign) != ValueAssignment:
					# TypeAssignemnts: generate_classes()
					continue
				#TODO# Need generic mapping to DER values
				self.pygenValueAssignment (assign)

	def pygenValueAssignment (self, node):
		# We only found INTEGER and OBJECTIDENTIFIER in RFCs
		# Note that these forms are computed while loading, so not fast
		cls = tosym (node.type_decl)
		var = tosym (node.value_name)
		if cls == 'INTEGER':
			val = self.pyvalInteger (node.value)
			cls = '_api.ASN1Integer'
		elif cls == 'OBJECTIDENTIFIER':
			val = self.pyvalOID (node.value)
			cls = '_api.ASN1OID'
		else:
			val = 'MAP2DER("""' + str (node.value) + '""")'
		self.comment (str (node))
		self.writeln (var + ' = ' + cls + ' (' + val + ')')
		self.writeln ()

	def pyvalInteger (self, valnode):
		return '_api.der_pack_INTEGER (' + str (int (valnode)) + ', hdr=True)'

	def pyvalOID (self, valnode):
		retc = []
		for oidcompo in valnode.components:
			if type (oidcompo) == NameForm:
				retc.append ('_api.der_unpack_OID (' + tosym (oidcompo.name) + '.get())')
			elif type (oidcompo) == NumberForm:
				retc.append ("'" + str (oidcompo.value) + "'")
			elif type (oidcompo) == NameAndNumberForm:
				retc.append ("'" + str (oidcompo.number) + "'")
		retval = " + '.' + ".join (retc)
		retval = '_api.der_pack_OID (' + retval.replace ("' + '", '') + ', hdr=True)'
		return retval

	def generate_classes (self):
		self.writeln ('#')
		self.writeln ('# Classes for ASN.1 type assignments')
		self.writeln ('#')
		self.writeln ()
		for assigncompos in dependency_sort(self.semamod.assignments):
			for assign in assigncompos:
				if type (assign) != TypeAssignment:
					# ValueAssignment: generate_values()
					continue
				self.pygenTypeAssignment (assign)

	def pygenTypeAssignment (self, node):
		def pymap_packer (pck, ln='\n        '):
			retval = '(' + ln
			pck = pck + [ 'DER_PACK_END' ]
			comma = ''
			for pcke in pck:
				pcke = pcke.replace ('DER_', '_api.DER_')
				retval += comma + 'chr(' + pcke + ')'
				comma = ' +' + ln
			retval += ' )'
			return retval
		def pymap_recipe (recp, ln='\n    '):
			if type (recp) == int:
				retval = str (recp)
			elif recp [0] == '_NAMED':
				(_NAMED,map) = recp
				ln += '    '
				retval = "('_NAMED', {"
				comma = False
				for (fld,fldrcp) in map.items ():
					if comma:
						retval += ',' + ln
					else:
						retval += ln
					retval += "'" + tosym (fld) + "': "
					retval += pymap_recipe (fldrcp, ln)
					comma = True
				retval += ' } )'
			elif recp [0] in ['_SEQOF','_SETOF']:
				(_STHOF,allidx,pck,inner_recp) = recp
				ln += '    '
				retval = "('" + _STHOF + "', "
				retval += str (allidx) + ', '
				retval += pymap_packer (pck, ln) + ',' + ln
				retval += pymap_recipe (inner_recp, ln) + ' )'
			elif recp [0] == '_TYPTR':
				(_TYPTR,cls,ofs) = recp
				retval = "('_TYPTR'," + cls.__name__ + ',' + str (ofs) + ')'
			else:
				(usertp,idx) = recp
				retval = repr (recp)
			return retval
		def pygen_class (clsnm, tp, pck, recp, numcrs):
			#TODO# Sometimes, ASN1Atom may have a specific supertp
			supertp = '_api.' + tp
			self.writeln ('class ' + clsnm + ' (' + supertp + '):')
			if tp not in ['ASN1SequenceOf','ASN1SetOf']:
				self.writeln ('    _der_packer = ' + pymap_packer (pck))
			if tp not in ['ASN1Atom']:
				self.writeln ('    _recipe = ' + pymap_recipe (recp))
			if False:
				#TODO# Always fixed or computed
				self.writeln ('    _numcursori = ' + str (numcrs))
			if False:
				#TODO# Perhaps needed at some point?
				self.writeln ('    pass')
			self.writeln ()
		self.cursor_offset = 0
		self.nested_typerefs = 0
		self.nested_typecuts = 0
		self.comment (str (node))
		(pck,recp) = self.generate_pytype (node.type_decl)
		if type (recp) == int:
			tp = 'ASN1Atom'
		elif recp [0] == '_NAMED':
			tp = 'ASN1ConstructedType'
		elif recp [0] == '_SEQOF':
			tp = 'ASN1SequenceOf'
		elif recp [0] == '_SETOF':
			tp = 'ASN1SetOf'
		elif recp [0] == '_TYPTR':
			(_TYPTR,cls,ofs) = recp
			tp = str (cls)
		else:
			(usrtp,idx) = recp
			tp = usrtp
		numcrs = self.cursor_offset
		pygen_class (tosym (node.type_name), tp, pck, recp, numcrs)

	def generate_pytype (self, node, **subarg):
		#DEBUG# sys.stderr.write ('Node = ' + str (node) + '\n')
		tnm = type (node)
		if tnm not in self.funmap_pytype.keys ():
			raise Exception ('Failure to generate a python type for ' + str (tnm))
		return self.funmap_pytype [tnm] (node, **subarg)

	def pytypeDefinedType (self, node, **subarg):
		#TODO# Really stop recursion here?!?
		if self.nested_typecuts > 0:
			#TODO# And not self.nested_typerefs > 0
			# We are about to recurse on self.nested_typerefs
			# but the recursion for self.nested_typecuts
			# has also occurred, so we can cut off recursion
			#TODO# Offset should be properly incremented???
			ofs = self.cursor_offset
			#TODO# Why increase cursor for a type reference?!?
			self.cursor_offset += 1
			return ([],(tosym (node.type_name), ofs))
		modnm = node.module_name
		if modnm is None:
			syms = self.semamod.imports.symbols_imported
			for mod in syms.keys ():
				if node.type_name in syms [mod]:
					modnm = mod.lower ()
					break
		if modnm is None:
			modnm = self.unit.lower ()
		if not self.refmods.has_key (modnm):
			raise Exception ('Module name "%s" not found' % modnm)
		popunit = self.unit
		popsema = self.semamod
		popcofs = self.cursor_offset
		#TODO# cursor_offset?
		self.unit = modnm
		self.semamod = self.refmods [modnm]
		self.nested_typerefs = self.nested_typerefs + 1
		thetype = self.refmods [modnm].user_types () [node.type_name]
		(pck,recp) = self.generate_pytype (thetype, **subarg)
		self.nested_typerefs = self.nested_typerefs - 1
		#TODO# cursor_offset?
		#TODO# recp should reference the class?
		self.semamod = popsema
		self.unit = popunit
		return (pck,recp)

	def pytypeSimple (self, node, implicit_tag=None):
		simptp = node.type_name.replace (' ', '').upper ()
		if simptp == 'ANY':
			# ANY counts as self.nested_typecuts but does not
			# have subtypes to traverse, so no attention to
			# recursion cut-off is needed or even possible here
			pck = [ 'DER_PACK_ANY' ]
			if implicit_tag:
				# Can't have an implicit tag around ANY
				pck = [ 'DER_PACK_ENTER | ' + implicit_tag ] + pck + [ 'DER_PACK_LEAVE' ]
		else:
			if not implicit_tag:
				implicit_tag = 'DER_TAG_' + simptp
			pck = [ 'DER_PACK_STORE | ' + implicit_tag ]
		recp = self.cursor_offset
		self.cursor_offset = recp + 1
		return (pck,recp)

	def pytypeTagged (self, node, implicit_tag=None):
		mytag = 'DER_TAG_' + (node.class_name or 'CONTEXT') + '(' + node.class_number + ')'
		if self.semamod.resolve_tag_implicity (node.implicity, node.type_decl) == TagImplicity.IMPLICIT:
			# Tag implicitly by handing mytag down to type_decl
			(pck,recp) = self.generate_pytype (node.type_decl,
							implicit_tag=mytag)
		else:
			# Tag explicitly by wrapping mytag around the type_decl
			(pck,recp) = self.generate_pytype (node.type_decl)
			pck = [ 'DER_PACK_ENTER | ' + mytag ] + pck + [ 'DER_PACK_LEAVE' ]
		if implicit_tag:
			# Can't nest implicit tags, so wrap surrounding ones
			pck = [ 'DER_PACK_ENTER | ' + implicit_tag ] + pck + [ 'DER_PACK_LEAVE' ]
		return (pck,recp)

	def pytypeNamedType (self, node,**subarg):
		#TODO# Ignore field name... or should be we use it any way?
		return self.generate_pytype (node.type_decl,**subarg)

	def pyhelpConstructedType (self, node):
		pck = []
		recp = {}
		for comp in node.components:
			if isinstance(comp, ExtensionMarker):
				#TODO# ...ASN.1 extensions...
				continue
			if isinstance (comp, ComponentType) and comp.components_of_type is not None:
				#TODO# ...COMPONENTS OF...
				continue
			(pck1,stru1) = self.generate_pytype (comp.type_decl)
			pck = pck + pck1
			recp [tosym (comp.identifier)] = stru1
		return (pck,('_NAMED',recp))

	def pytypeChoice (self, node, implicit_tag=None):
		(pck,recp) = self.pyhelpConstructedType (node)
		pck = [ 'DER_PACK_CHOICE_BEGIN' ] + pck + [ 'DER_PACK_CHOICE_END' ]
		if implicit_tag:
			# Can't have an implicit tag around a CHOICE
			pck = [ 'DER_PACK_ENTER | ' + implicit_tag ] + pck + [ 'DER_PACK_LEAVE' ]
		return (pck,recp)

	def pytypeSequence (self, node, implicit_tag='DER_TAG_SEQUENCE'):
		(pck,recp) = self.pyhelpConstructedType (node)
		pck = [ 'DER_PACK_ENTER | ' + implicit_tag ] + pck + [ 'DER_PACK_LEAVE' ]
		return (pck,recp)

	def pytypeSet (self, node, implicit_tag='DER_TAG_SET'):
		(pck,recp) = self.pyhelpConstructedType (node)
		pck = [ 'DER_PACK_ENTER | ' + implicit_tag ] + pck + [ 'DER_PACK_LEAVE' ]
		return (pck,recp)

	def pytypeSequenceOf (self, node, implicit_tag='DER_TAG_SEQUENCE'):
		allidx = self.cursor_offset
		self.cursor_offset += 1
		if self.nested_typerefs > 0 and self.nested_typecuts > 0:
			# We are about to recurse on self.nested_typecuts
			# but the recursion for self.nested_typerefs
			# has also occurred, so we can cut off recursion
			subpck = []
			subrcp = 666
		else:
			self.nested_typecuts = self.nested_typecuts + 1
			#TODO# push & reset self.cursor_offset
			(subpck,subrcp) = self.generate_pytype (node.type_decl)
			#TODO# pop self.cursor_offset
			self.nested_typecuts = self.nested_typecuts - 1
		pck = [ 'DER_PACK_STORE | ' + implicit_tag ]
		return (pck,('_SEQOF',allidx,subpck,subrcp))

	def pytypeSetOf (self, node, implicit_tag='DER_TAG_SET'):
		allidx = self.cursor_offset
		self.cursor_offset += 1
		if self.nested_typerefs > 0 and self.nested_typecuts > 0:
			# We are about to recurse on self.nested_typecuts
			# but the recursion for self.nested_typerefs
			# has also occurred, so we can cut off recursion
			subpck = []
			subrcp = 777
		else:
			self.nested_typecuts = self.nested_typecuts + 1
			#TODO# push & reset self.cursor_offset
			(subpck,subrcp) = self.generate_pytype (node.type_decl)
			#TODO# pop self.cursor_offset
			self.nested_typecuts = self.nested_typecuts - 1
		pck = [ 'DER_PACK_STORE | ' + implicit_tag ]
		return (pck,('_SETOF',allidx,subpck,subrcp))


"""The main program asn2quickder is called with one or more .asn1 files,
   the first of which is mapped to a C header file and the rest is
   loaded to fulfil dependencies.
"""

if len(sys.argv) < 2:
    sys.stderr.write('Usage: %s [-I incdir] ... main.asn1 [dependency.asn1] ...\n'
        % sys.argv [0])
    sys.exit(1)

defmods = {}
refmods = {}
incdirs = []
(opts,restargs) = getopt.getopt (sys.argv [1:], 'I:')
for (opt,optarg) in opts:
	if opt != '-I':
		sys.stderr.write ('Usage: ' + sys.argv [0] + ' [-I incdir] ... main.asn1 [dependency.asn1] ...\n')
		sys.exit (1)
	incdirs.append (optarg)
incdirs.append (os.path.curdir)
for file in restargs:
    modnm = os.path.basename (file).lower ()
    #TODO:DEBUG# print('Parsing ASN.1 syntaxdef for "%s"' % modnm)
    with open(file, 'r') as asn1fh:
        asn1txt  = asn1fh.read()
        asn1tree = parser.parse_asn1(asn1txt)
    #TODO:DEBUG# print('Building semantic model for "%s"' % modnm)
    asn1sem = build_semantic_model(asn1tree)
    defmods [os.path.basename (file)    ] = asn1sem [0]
    refmods [os.path.splitext (modnm)[0]] = asn1sem [0]
    #TODO:DEBUG# print('Realised semantic model for "%s"' % modnm)

imports = refmods.keys ()
while len (imports) > 0:
    dm = refmods [imports.pop (0).lower ()]
    for rm in dm.imports.symbols_imported.keys ():
	rm = rm.lower ()
	if not refmods.has_key (rm):
	    #TODO:DEBUG# print ('Importing ASN.1 include for "%s"' % rm)
	    modfh = None
	    for incdir in incdirs:
		try:
		    modfh = open (incdir + os.path.sep + rm + '.asn1', 'r')
		    break
		except IOError:
		    continue
	    if modfh is None:
		raise Exception ('No include file "%s.asn1" found' % rm)
	    asn1txt = modfh.read()
	    asn1tree = parser.parse_asn1(asn1txt)
	    #TODO:DEBUG# print ('Building semantic model for "%s"' % rm)
	    asn1sem = build_semantic_model(asn1tree)
	    refmods [rm] = asn1sem [0]
	    imports.append (rm)
	    #TODO:DEBUG# print('Realised semantic model for "%s"' % rm)

# Generate C header files
for modnm in defmods.keys ():
	#TODO:DEBUG# print ('Generating C header file for "%s"' % modnm)
	cogen = QuickDER2c (defmods [modnm], modnm, refmods)
	cogen.generate_head ()
	cogen.generate_overlay ()
	cogen.generate_pack ()
	cogen.generate_psub ()
	cogen.generate_tail ()
	cogen.close ()
	#TODO:DEBUG# print ('Ready with C header file for "%s"' % modnm)

# Generate Python modules
for modnm in defmods.keys ():
	#TODO:DEBUG# print ('Generating Python module for "%s"' % modnm)
	cogen = QuickDER2py (defmods [modnm], modnm, refmods)
	cogen.generate_head ()
	cogen.generate_classes ()
	cogen.generate_values ()
	cogen.generate_tail ()
	cogen.close ()
	#TODO:DEBUG# print ('Ready with Python module for "%s"' % modnm)

