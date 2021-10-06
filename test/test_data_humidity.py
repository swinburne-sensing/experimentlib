import unittest

from experimentlib.data import humidity, unit


class TestDataHumidity(unittest.TestCase):
    def test_rel_to_abs(self):
        rel_humid = unit.parse('100%')
        temp = unit.parse('30 degC')
        abs_humid = unit.parse('30.359 g/m^3')

        calc_abs_humid = humidity.rel_to_abs(temp, rel_humid)

        self.assertAlmostEqual(abs_humid.m_as(humidity.unit_abs), calc_abs_humid.m_as(humidity.unit_abs), 1)

    def test_abs_to_rel(self):
        rel_humid = unit.parse('100%')
        temp = unit.parse('30 degC')
        abs_humid = unit.parse('30.359 g/m^3')

        calc_rel_humid = humidity.abs_to_rel(temp, abs_humid)

        self.assertAlmostEqual(rel_humid.m_as(unit.dimensionless), calc_rel_humid.m_as(unit.dimensionless), 1)


if __name__ == '__main__':
    unittest.main()
