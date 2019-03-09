import unittest
from os import path
from quick_der.generators.source import QuickDER2source
from quick_der.main import realise

here = (path.dirname(path.realpath(__file__)))


class TestQuickDER2source(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo = path.join(here, '..', '..', 'rfc')
        asn_test = path.join(repo, 'rfc1422.asn1')
        cls.defmods, cls.refmods = realise([repo], [asn_test])

    def test_full(self):
        for modnm in self.defmods.keys():
            gen = QuickDER2source(self.defmods[modnm], modnm, self.refmods)
            gen.generate_head()
            gen.generate_pack()
            gen.generate_unpack()
            gen.generate_tail()
            gen.close()
