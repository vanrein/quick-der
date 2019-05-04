import unittest
from os import path
from quick_der.main import main

here = (path.dirname(path.realpath(__file__)))


class TestAsn2Quickder(unittest.TestCase):

    def test_test01(self):
        asn1_path = path.join(here, '..', 'data', 'test01.asn1')
        main('asn2quickder', [asn1_path])

    def test_test01a(self):
        asn1_path = path.join(here, '..', 'data', 'test01a.asn1')
        main('asn2quickder', [asn1_path])

    def test_test02(self):
        asn1_path = path.join(here, '..', 'data', 'test02.asn1')
        main('asn2quickder', [asn1_path])

    def test_test04(self):
        asn1_path = path.join(here, '..', 'data', 'test04.asn1')
        main('asn2quickder', [asn1_path])

    @unittest.skip('TODO: see issue #42')
    def test_test05(self):
        asn1_path = path.join(here, '..', 'data', 'test05.asn1')
        main('asn2quickder', [asn1_path])

    def test_kxover(self):
        asn1_path = path.join(here, '..', '..', 'arpa2', 'kxover.asn1')
        main('asn2quickder', ['-l', 'c', '-I', path.join(here, '..', '..', 'rfc'), asn1_path])


