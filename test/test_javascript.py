import unittest

from experimentlib.util import javascript


class TestUtilJavascript(unittest.TestCase):
    def test_parse_bool_true(self):
        parsed = javascript.parse_value('true')

        self.assertIsInstance(parsed, bool)
        self.assertTrue(parsed)

    def test_parse_bool_false(self):
        parsed = javascript.parse_value('false')

        self.assertIsInstance(parsed, bool)
        self.assertFalse(parsed)

    def test_parse_str(self):
        parsed = javascript.parse_value('"this is a string"')

        self.assertIsInstance(parsed, str)

    def test_parse_int(self):
        parsed = javascript.parse_value('123')

        self.assertIsInstance(parsed, int)

    def test_parse_float(self):
        parsed = javascript.parse_value('1.23456789')

        self.assertIsInstance(parsed, float)

    def test_parse_list_int(self):
        parsed = javascript.parse_value('[1,2,3]')

        self.assertIsInstance(parsed, list)
        self.assertSequenceEqual(parsed, [1, 2, 3])

    def test_parse_list_int_nested(self):
        parsed = javascript.parse_value('[1,[2,3],[4]]')

        self.assertIsInstance(parsed, list)
        self.assertSequenceEqual(parsed, [1, [2, 3], [4]])
