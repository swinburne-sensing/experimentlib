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
        self.assertEqual(test_qty.magnitude, 100.0)

        test_qty = unit.parse(100.0)

        self.assertIsInstance(test_qty, unit.Quantity)
        self.assertTrue(test_qty.unitless)
        self.assertEqual(test_qty.magnitude, 100.0)

    def test_parsing_int(self):
        test_qty = unit.parse(100, 'm')

        self.assertIsInstance(test_qty, unit.Quantity)
        self.assertTrue(test_qty.is_compatible_with('m'))
        self.assertEqual(test_qty.magnitude, 100)

        test_qty = unit.parse(100)

        self.assertIsInstance(test_qty, unit.Quantity)
        self.assertTrue(test_qty.unitless)
        self.assertEqual(test_qty.magnitude, 100)

    def test_parsing_exp(self):
        test_qty = unit.parse('1×10³', 'm')

        self.assertIsInstance(test_qty, unit.Quantity)
        self.assertTrue(test_qty.is_compatible_with('m'))
        self.assertEqual(test_qty.magnitude, 1000)

    def test_parsing_quantity(self):
        test_input = unit.Quantity('1 m')

        test_qty = unit.parse(test_input, 'mm')

        self.assertIsInstance(test_qty, unit.Quantity)
        self.assertTrue(test_qty.is_compatible_with('m'))
        self.assertEqual(test_qty.magnitude, 1000)

    def test_parsing_percent_str(self):
        test_qty = unit.parse('50%')

        self.assertIsInstance(test_qty, unit.Quantity)
        self.assertTrue(test_qty.dimensionless)
        self.assertEqual(test_qty.m_as('dimensionless'), 0.5)
        self.assertEqual(test_qty.m_as('pct'), 50)

    def test_parsing_percent_float(self):
        for n in range(100):
            n *= 1 / 100
            test_qty = unit.parse(n)

            self.assertTrue(isinstance(test_qty, unit.Quantity))
            self.assertTrue(test_qty.dimensionless)
            self.assertEqual(test_qty.m_as('dimensionless'), n)
            self.assertEqual(test_qty.m_as('pct'), n * 100)

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

    def test_parsing_unit_error_none(self):
        with self.assertRaises(unit.QuantityParseError):
            unit.parse_unit(None)

    def test_print_numeric(self):
        self.assertEqual(str(unit.parse(0.5)), '0.5')
        self.assertEqual(str(unit.parse(1.0)), '1')
        self.assertEqual(str(unit.parse(1.010)), '1.01')
        self.assertEqual(str(unit.parse(1e3)), '1×10³')

    def test_print_percent(self):
        self.assertEqual(str(unit.parse(1, '%')), '1%')
        self.assertEqual(str(unit.parse(50, '%')), '50%')
        self.assertEqual(str(unit.parse(100, '%')), '100%')
        self.assertEqual(str(unit.parse(1).to('pct')), '100%')
        self.assertEqual(str(unit.parse(1).to('ppm')), '100%')
        self.assertEqual(str(unit.parse(1e-6)), '1×10⁻⁶')

    def test_time(self):
        self.assertEqual(str(unit.parse(1000, 's')), '1000 s')


if __name__ == '__main__':
    unittest.main()
