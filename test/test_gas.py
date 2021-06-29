import unittest

from experimentlib.data import gas, unit


class TestDataGas(unittest.TestCase):
    def test_mix(self):
        gas_parse_a = gas.Mixture.from_str('1% hydrogen, air')
        gas_parse_b = gas.Mixture.from_str('1% methane, air')

        gas_parse_mixed = 0.25 * gas_parse_a + 0.75 * gas_parse_b

        self.assertTrue(len(gas_parse_mixed.components) == 2)

        self.assertTrue(gas_parse_mixed.components[0].quantity.m_as(unit.dimensionless) == 0.0075)
        self.assertTrue(gas_parse_mixed.components[0].properties == gas.registry.methane)

        self.assertTrue(gas_parse_mixed.components[1].quantity.m_as(unit.dimensionless) == 0.0025)
        self.assertTrue(gas_parse_mixed.components[1].properties == gas.registry.hydrogen)

        self.assertAlmostEqual(gas_parse_mixed.balance.quantity.m_as(unit.dimensionless), 0.99, 6)
        self.assertTrue(gas_parse_mixed.balance.properties == gas.registry.air)

    def test_mix_over_limit(self):
        with self.assertRaises(gas.CalculationError):
            gas.Mixture.from_str('101% hydrogen, air')

    def test_mix_incompatible(self):
        a = gas.Mixture.from_str('1% hydrogen, air')
        b = gas.Mixture.from_str('1% hydrogen, nitrogen')

        with self.assertRaises(gas.MixingError):
            a + b

    def test_gcf(self):
        gas_air = gas.Component(1, gas.registry.air)
        self.assertAlmostEqual(gas_air.gcf, 1, delta=0.01)

        gas_helium = gas.Component(1, gas.registry.helium)
        self.assertAlmostEqual(gas_helium.gcf, 1.45, delta=0.01)

        gas_ammonia = gas.Component(1, gas.registry.ammonia)
        self.assertAlmostEqual(gas_ammonia.gcf, 0.73, delta=0.01)

    def test_parse(self):
        gas_h2_air_10000ppm = gas.Mixture.auto_balance([gas.Component(0.01, gas.registry.hydrogen)], gas.registry.air)
        gas_h2_air_1000ppm = gas.Mixture.auto_balance([gas.Component(0.001, gas.registry.hydrogen)], gas.registry.air)

        gas_str_list = [
            ('1% hydrogen, air',
             gas_h2_air_10000ppm),
            ('1 kppm Hydrogen (H_2), 99.9% Air',
             gas_h2_air_1000ppm),
            ('1% Hydrogen (H_2), 99% Air',
             gas_h2_air_10000ppm),
            ('1.05% Carbon-dioxide (CO_2), 99% Air',
             gas.Mixture.auto_balance([gas.Component(0.0105, gas.registry.carbon_dioxide)], gas.registry.air)),
            ('100% Air',
             gas.Mixture.auto_balance([], gas.registry.air)),
            ('100% Humid Air',
             gas.Mixture.auto_balance([], gas.registry.humid_air)),
            ('12 ppm Nitrogen-dioxide (NO_2), 100% Air',
             gas.Mixture.auto_balance([gas.Component(12e-6, gas.registry.nitrogen_dioxide)], gas.registry.air)),
            ('50 ppm Acetone, 100% Air',
             gas.Mixture.auto_balance([gas.Component(50e-6, gas.registry.acetone)], gas.registry.air)),
            ('50 ppm Ammonia (NH_3), 100% Air',
             gas.Mixture.auto_balance([gas.Component(50e-6, gas.registry.ammonia)], gas.registry.air)),
            ('50 ppm Methane (CH_4), 100% Air',
             gas.Mixture.auto_balance([gas.Component(50e-6, gas.registry.methane)], gas.registry.air))
        ]

        for gas_str, gas_mix in gas_str_list:
            gas_parse = gas.Mixture.from_str(gas_str)

            self.assertSequenceEqual(gas_parse.components, gas_mix.components)
            self.assertTrue(gas_parse.balance == gas_mix.balance)

    def test_parsing_unknown(self):
        with self.assertRaises(gas.UnknownGas):
            gas.Mixture.from_str('1% soup, air')


if __name__ == '__main__':
    unittest.main()
