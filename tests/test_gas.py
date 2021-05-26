import unittest

from experimentlib.data import gas


class MyTestCase(unittest.TestCase):
    def test_humidity(self):
        gas_dry = gas.registry.air
        gas_humid = gas.registry.humid_air


if __name__ == '__main__':
    unittest.main()
