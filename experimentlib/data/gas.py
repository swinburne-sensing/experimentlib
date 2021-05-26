from __future__ import annotations

import enum
import re
from typing import List, Optional

import attr

from experimentlib.data import unit


class GasError(Exception):
    pass


class GasMixError(GasError):
    pass


class GasRatioError(GasError):
    pass


class UnknownGas(GasError):
    pass


class MolecularStructure(enum.Enum):
    """ Molecular structure gas constants.

    Reference: MKS (https://www.mksinst.com/n/flow-measurement-control-frequently-asked-questions)
    """
    MONOTOMIC = 1.03
    DIATOMIC = 1
    TRIATOMIC = 0.941
    POLYATOMIC = 0.88


@attr.s(frozen=True)
class ChemicalProperties(object):
    UNIT_DENSITY = unit.registry.g / unit.registry.L
    UNIT_SPECIFIC_HEAT = unit.registry.cal / unit.registry.g

    # Gas name
    name: str = attr.ib()

    # Gas chemical symbol
    symbol: Optional[str] = attr.ib(default=None)

    # Chemical properties
    density: unit.Quantity = attr.ib(converter=unit.converter_optional(UNIT_DENSITY), default=None, kw_only=True)
    molecular_structure: MolecularStructure = attr.ib(default=None, kw_only=True)
    specific_heat: unit.Quantity = attr.ib(converter=unit.converter_optional(UNIT_SPECIFIC_HEAT), default=None,
                                           kw_only=True)

    # Inert gas flag
    inert: bool = attr.ib(default=False, kw_only=True)

    # Humidity flag
    humid: bool = attr.ib(default=False, kw_only=True)

    def __str__(self):
        if self.symbol is not None:
            return self.symbol
        else:
            return self.name


class Registry(object):
    air = ChemicalProperties('Air', molecular_structure=MolecularStructure.DIATOMIC, specific_heat=0.24, density=1.293, inert=True)
    acetone = ChemicalProperties('Acetone', '(CH_3)_2CO', molecular_structure=MolecularStructure.POLYATOMIC, specific_heat=0.51,
                                 density=0.21)
    ammonia = ChemicalProperties('Ammonia', 'NH_3', molecular_structure=MolecularStructure.POLYATOMIC, specific_heat=0.492,
                                 density=0.76)
    argon = ChemicalProperties('Argon', 'Ar', molecular_structure=MolecularStructure.MONOTOMIC, specific_heat=0.1244, density=1.782,
                               inert=True)
    arsine = ChemicalProperties('Arsine', molecular_structure=MolecularStructure.POLYATOMIC, specific_heat=0.1167, density=3.478)
    bromine = ChemicalProperties('Bromine', 'BR_2', molecular_structure=MolecularStructure.DIATOMIC, specific_heat=0.0539,
                                 density=7.13)
    carbon_dioxide = ChemicalProperties('Carbon-dioxide', 'CO_2', molecular_structure=MolecularStructure.TRIATOMIC,
                                        specific_heat=0.2016, density=1.964)
    carbon_monoxide = ChemicalProperties('Carbon-monoxide', 'CO', molecular_structure=MolecularStructure.DIATOMIC,
                                         specific_heat=0.2488, density=1.25)
    carbon_tetrachloride = ChemicalProperties('Carbon-tetrachloride', molecular_structure=MolecularStructure.POLYATOMIC,
                                              specific_heat=0.1655, density=6.86)
    carbon_tetraflouride = ChemicalProperties('Carbon-tetraflouride', molecular_structure=MolecularStructure.POLYATOMIC,
                                              specific_heat=0.1654, density=3.926)
    chlorine = ChemicalProperties('Chlorine', 'Cl_2', molecular_structure=MolecularStructure.DIATOMIC, specific_heat=0.1144,
                                  density=3.163)
    cyanogen = ChemicalProperties('Cyanogen', molecular_structure=MolecularStructure.POLYATOMIC, specific_heat=0.2613, density=2.322)
    deuterium = ChemicalProperties('Deuterium', 'H_2/D_2', molecular_structure=MolecularStructure.DIATOMIC, specific_heat=1.722,
                                   density=0.1799)
    ethane = ChemicalProperties('Ethane', 'C_2H_6', molecular_structure=MolecularStructure.POLYATOMIC, specific_heat=0.4097,
                                density=1.342)
    fluorine = ChemicalProperties('Fluorine', 'F_2', molecular_structure=MolecularStructure.DIATOMIC, specific_heat=0.1873,
                                  density=1.695)
    helium = ChemicalProperties('Helium', 'He', molecular_structure=MolecularStructure.MONOTOMIC, specific_heat=1.241,
                                density=0.1786)
    hexane = ChemicalProperties('Hexane', 'C_6H14', molecular_structure=MolecularStructure.POLYATOMIC, specific_heat=0.54,
                                density=0.672)
    hydrogen = ChemicalProperties('Hydrogen', 'H_2', molecular_structure=MolecularStructure.DIATOMIC, specific_heat=3.3852,
                                  density=0.0899)
    hydrogen_chloride = ChemicalProperties('Hydrogen-chloride', 'HCl', molecular_structure=MolecularStructure.DIATOMIC,
                                           specific_heat=0.1912, density=1.627)
    hydrogen_fluoride = ChemicalProperties('Hydrogen-fluoride', 'HF', molecular_structure=MolecularStructure.DIATOMIC,
                                           specific_heat=0.3479, density=0.893)
    methane = ChemicalProperties('Methane', 'CH_4', molecular_structure=MolecularStructure.POLYATOMIC, specific_heat=0.5223,
                                 density=0.716)
    neon = ChemicalProperties('Neon', 'Ne', molecular_structure=MolecularStructure.MONOTOMIC, specific_heat=0.246, density=0.9)
    nitric_oxide = ChemicalProperties('Nitric-oxide', 'NO', molecular_structure=MolecularStructure.DIATOMIC, specific_heat=0.2328,
                                      density=1.339)
    nitric_oxides = ChemicalProperties('Nitric-oxides', 'NO_x')
    nitrogen = ChemicalProperties('Nitrogen', 'N_2', molecular_structure=MolecularStructure.DIATOMIC, specific_heat=0.2485,
                                  density=1.25, inert=True)
    nitrogen_dioxide = ChemicalProperties('Nitrogen-dioxide', 'NO_2', molecular_structure=MolecularStructure.TRIATOMIC,
                                          specific_heat=0.1933, density=2.052)
    nitrous_oxide = ChemicalProperties('Nitrous-oxide', 'N_2O', molecular_structure=MolecularStructure.TRIATOMIC,
                                       specific_heat=0.2088, density=1.964)
    oxygen = ChemicalProperties('Oxygen', 'O_2', molecular_structure=MolecularStructure.DIATOMIC, specific_heat=0.2193,
                                density=1.427)
    phosphine = ChemicalProperties('Phosphine', 'PH_3', molecular_structure=MolecularStructure.POLYATOMIC, specific_heat=0.2374,
                                   density=1.517)
    propane = ChemicalProperties('Propane', 'C_3H_8', molecular_structure=MolecularStructure.POLYATOMIC, specific_heat=0.3885,
                                 density=1.967)
    propylene = ChemicalProperties('Propylene', 'C_3H_6', molecular_structure=MolecularStructure.POLYATOMIC, specific_heat=0.3541,
                                   density=1.877)
    sulfur_hexafluoride = ChemicalProperties('Sulfur Hexaflouride', 'SF_6', molecular_structure=MolecularStructure.POLYATOMIC,
                                             specific_heat=0.1592, density=6.516)
    xenon = ChemicalProperties('Xenon', 'Xe', molecular_structure=MolecularStructure.MONOTOMIC, specific_heat=0.0378, density=5.858)

    humid_air = ChemicalProperties('Humid Air', molecular_structure=MolecularStructure.DIATOMIC, specific_heat=0.24, density=1.293,
                                   inert=True, humid=True)
    humid_argon = ChemicalProperties('Humid Argon', 'Ar', molecular_structure=MolecularStructure.MONOTOMIC, specific_heat=0.1244,
                                     density=1.782, inert=True, humid=True)
    humid_nitrogen = ChemicalProperties('Humid Nitrogen', 'N_2', molecular_structure=MolecularStructure.DIATOMIC,
                                        specific_heat=0.2485, density=1.25, inert=True, humid=True)


@attr.s(frozen=True)
class Component(object):
    # Actual concentration
    quantity: unit.Quantity = attr.ib(converter=unit.Quantity(unit.registry.dimensionless))

    # Gas type
    properties: ChemicalProperties = attr.ib()

    def __attrs_post_init__(self):
        # Scale concentration to look nice
        magnitude = abs(self.quantity.m_as(unit.registry.dimensionless))

        if magnitude >= 1e-4:
            units = unit.registry.pct
        elif magnitude >= 1e-6:
            units = unit.registry.ppm
        elif magnitude > 0:
            units = unit.registry.ppb
        else:
            units = unit.registry.dimensionless

        object.__setattr__(self, 'quantity', self.quantity.to(units))

    def __rmul__(self, other):
        return Component(other * self.quantity, self.properties)

    def __str__(self):
        return f"{self.quantity!s} {self.properties!s}"


@attr.s(frozen=True)
class Mixture(object):
    # Gases in mixture
    components: List[Component] = attr.ib()

    # Balance gas
    balance: ChemicalProperties = attr.ib()

    _GAS_CONCENTRATION_PATTERN = re.compile(r'^([\d]+\.?[\d]*)[ ]?([%\w]+) ([\w\s-]+)')

    @property
    def balance_ratio(self) -> unit.Quantity:
        ratio = 1

        for component in self.components:
            ratio -= component.quantity

        return ratio

    @property
    def humid(self) -> bool:
        """ True if no component in the gas carries humidity.

        :return:
        """
        return any((component.properties.humid for component in self.components)) or self.balance.humid

    @property
    def humid_ratio(self) -> unit.Quantity:
        ratio = 0

        for component in self.components:
            if component.properties.humid:
                ratio += component.quantity

        return ratio

    @property
    def inert(self) -> bool:
        """ True if all gases in mixture are inert.

        :return:
        """
        return all((component.properties.inert for component in self.components)) and self.balance.inert

    @property
    def gcf(self) -> float:
        """

        :return:
        """
        pass

    def __str__(self):
        if len(self.components) > 0:
            return f"{', '.join(map(str, self.components))}"
        else:
            return str(self.balance)

    def __rmul__(self, other):
        if isinstance(other, int):
            other = float(other)
        elif isinstance(other, unit.Quantity):
            if not other.dimensionless:
                raise GasRatioError('Multiply factor must be dimensionless')

            # Cast to magnitude
            other = other.to('dimensionless').quantity

        if not isinstance(other, float):
            raise GasRatioError('Incompatible multiplication factor')

        scaled_gases = [other * gas for gas in self.components]

        return Mixture(scaled_gases, self.balance)

    def __add__(self, other):
        gas_conc_dict = {}

        if not isinstance(other, Mixture):
            raise GasMixError('Incompatible class')

        if self.balance != other.balance:
            raise GasMixError(f"Incompatible balance components {self.balance} != {other.balance}")

        for gas_conc in self.components + other.components:
            if gas_conc.properties in gas_conc_dict:
                gas_conc_dict[gas_conc.properties] += gas_conc.quantity
            else:
                gas_conc_dict[gas_conc.properties] = gas_conc.quantity

        return Mixture([Component(conc, gas) for gas, conc in gas_conc_dict.items()], self.balance)

    @classmethod
    def from_str(cls, gas_list_str: str) -> Mixture:
        gases: List[Component] = []

        # Replace percentages for parsing
        gas_list = [x.strip() for x in gas_list_str.split(',')]

        # Parse components
        for gas_str in gas_list:
            gas_comp = cls._GAS_CONCENTRATION_PATTERN.match(gas_str)

            if gas_comp is not None:
                concentration = unit.Quantity(gas_comp[1] + ' ' + gas_comp[2])
                gas_name = gas_comp[3].strip()
            else:
                concentration = unit.Quantity(1, unit.registry.dimensionless)
                gas_name = gas_str

            gas = None

            if gas_name.lower() in library:
                gas = library[gas_name.lower()]
            else:
                for gas_obj in library.values():
                    if gas_name == gas_obj.name:
                        gas = gas_obj
                        break

            if gas is None:
                raise UnknownGas(f"Unknown gas \"{gas_name}\" (from: \"{gas_str}\")")

            gases.append(Component(concentration, gas))

        return Mixture(gases[:-1], gases[-1].properties)
