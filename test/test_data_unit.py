import unittest

from experimentlib.data import unit


class TestDataUnit(unittest.TestCase):
    def test_parsing_str(self):
        test_qty = unit.parse('100 degC', 'kelvin')

        self.assertIsInstance(test_qty, unit.Quantity)
        self.assertEqual(test_qty.units, unit.registry.kelvin)
        self.assertAlmostEqual(test_qty.m_as('kelvin'), 373.15, 2)
        self.assertAlmostEqual(test_qty.m_as('degC'), 100, 2)

        test_qty = unit.parse('100K')

        self.assertIsInstance(test_qty, unit.Quantity)
        self.assertEqual(test_qty.units, unit.registry.kelvin)
        self.assertAlmostEqual(test_qty.m_as('kelvin'), 100, 2)
        self.assertAlmostEqual(test_qty.m_as('degC'), -173.15, 2)

    def test_parsing_float(self):
        test_qty = unit.parse(100.0, 'm')

        self.assertIsInstance(test_qty, unit.Quantity)
        self.assertTrue(test_qty.is_compatible_with('m'))
        self.assertEqual(test_qty.quantity, 100.0)

        test_qty = unit.parse(100.0)

        self.assertIsInstance(test_qty, unit.Quantity)
        self.assertTrue(test_qty.unitless)
        self.assertEqual(test_qty.quantity, 100.0)

    def test_parsing_int(self):
        test_qty = unit.parse(100, 'm')

        self.assertIsInstance(test_qty, unit.Quantity)
        self.assertTrue(test_qty.is_compatible_with('m'))
        self.assertEqual(test_qty.quantity, 100)

        test_qty = unit.parse(100)

        self.assertIsInstance(test_qty, unit.Quantity)
        self.assertTrue(test_qty.unitless)
        self.assertEqual(test_qty.quantity, 100)

    def test_parsing_quantity(self):
        test_input = unit.Quantity('1 m')

        test_qty = unit.parse(test_input, 'mm')

        self.assertIsInstance(test_qty, unit.Quantity)
        self.assertTrue(test_qty.is_compatible_with('m'))
        self.assertEqual(test_qty.quantity, 1000)

    def test_parsing_percent_str(self):
        test_qty = unit.parse('50%')

        self.assertIsInstance(test_qty, unit.Quantity)
        self.assertTrue(test_qty.dimensionless)
        self.assertEqual(test_qty.m_as('dimensionless'), 0.5)
        self.assertEqual(test_qty.m_as('pct'), 50)

    def test_parsing_percent_float(self):
        test_qty = unit.parse(0.5)

        self.assertTrue(isinstance(test_qty, unit.Quantity))
        self.assertTrue(test_qty.dimensionless)
        self.assertEqual(test_qty.m_as('dimensionless'), 0.5)
        self.assertEqual(test_qty.m_as('pct'), 50)

    def test_parsing_error_unit(self):
        test_input = unit.Quantity('50 m')

        with self.assertRaises(unit.QuantityParseError):
            unit.parse(test_input, 'Hz')

    def test_parsing_error_class(self):
        with self.assertRaises(unit.QuantityParseError):
            unit.parse(self)

    def test_parsing_error_none(self):
        with self.assertRaises(unit.QuantityParseError):
            unit.parse(None)


if __name__ == '__main__':
    unittest.main()
