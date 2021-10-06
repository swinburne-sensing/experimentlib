from __future__ import annotations

import enum
import re
from typing import List, Optional, Union

import attr

from experimentlib.data import unit
from experimentlib.util import storage


class GasError(Exception):
    pass


class CalculationError(GasError):
    pass


class NegativeQuantityError(CalculationError):
    pass


class MixingError(GasError):
    pass


class ParserError(GasError):
    pass


class UnknownGas(ParserError):
    pass


class MolecularStructure(enum.Enum):
    """ Molecular structure gas constants.

    Reference: MKS (https://www.mksinst.com/n/flow-measurement-control-frequently-asked-questions)
    """
    MONATOMIC = 1.03
    DIATOMIC = 1
    TRIATOMIC = 0.941
    POLYATOMIC = 0.88


@attr.s(frozen=True)
class ChemicalProperties(storage.RegistryEntry):
    # Gas name
    name: str = attr.ib()

    # Gas chemical symbol
    symbol: Optional[str] = attr.ib(default=None)

    # Chemical properties
    molecular_structure: MolecularStructure = attr.ib(default=None, kw_only=True)
    specific_heat: Union[unit.TYPE_PARSE_VALUE, unit.Quantity] = attr.ib(
        converter=unit.converter(unit.registry.cal / unit.registry.g, True), default=None, kw_only=True)
    density: Union[unit.TYPE_PARSE_VALUE, unit.Quantity] = attr.ib(
        converter=unit.converter(unit.registry.g / unit.registry.L, True), default=None, kw_only=True)

    # Inert gas flag
    inert: bool = attr.ib(default=False, kw_only=True)

    # Humidity flag
    humid: bool = attr.ib(default=False, kw_only=True)

    def __str__(self):
        if self.symbol is not None:
            return self.symbol
        else:
            return self.name

    @property
    def registry_key(self) -> str:
        return self.name


registry = storage.Registry([
    ChemicalProperties(
        'Air',
        molecular_structure=MolecularStructure.DIATOMIC,
        specific_heat=0.24,
        density=1.293,
        inert=True
    ),
    ChemicalProperties(
        'Acetone', '(CH_3)_2CO',
        molecular_structure=MolecularStructure.POLYATOMIC,
        specific_heat=0.51,
        density=0.21
    ),
    ChemicalProperties(
        'Ammonia', 'NH_3',
        molecular_structure=MolecularStructure.POLYATOMIC,
        specific_heat=0.492,
        density=0.76
    ),
    ChemicalProperties(
        'Argon', 'Ar',
        molecular_structure=MolecularStructure.MONATOMIC,
        specific_heat=0.1244,
        density=1.782,
        inert=True
    ),
    ChemicalProperties(
        'Arsine', molecular_structure=MolecularStructure.POLYATOMIC,
        specific_heat=0.1167,
        density=3.478
    ),
    ChemicalProperties(
        'Bromine', 'BR_2',
        molecular_structure=MolecularStructure.DIATOMIC,
        specific_heat=0.0539,
        density=7.13
    ),
    ChemicalProperties(
        'Carbon-dioxide', 'CO_2',
        molecular_structure=MolecularStructure.TRIATOMIC,
        specific_heat=0.2016,
        density=1.964
    ),
    ChemicalProperties(
        'Carbon-monoxide', 'CO',
        molecular_structure=MolecularStructure.DIATOMIC,
        specific_heat=0.2488,
        density=1.25
    ),
    ChemicalProperties(
        'Carbon-tetrachloride',
        molecular_structure=MolecularStructure.POLYATOMIC,
        specific_heat=0.1655,
        density=6.86
    ),
    ChemicalProperties(
        'Carbon-tetraflouride',
        molecular_structure=MolecularStructure.POLYATOMIC,
        specific_heat=0.1654,
        density=3.926
    ),
    ChemicalProperties(
        'Chlorine', 'Cl_2',
        molecular_structure=MolecularStructure.DIATOMIC,
        specific_heat=0.1144,
        density=3.163
    ),
    ChemicalProperties(
        'Cyanogen',
        molecular_structure=MolecularStructure.POLYATOMIC,
        specific_heat=0.2613,
        density=2.322
    ),
    ChemicalProperties(
        'Deuterium', 'H_2/D_2',
        molecular_structure=MolecularStructure.DIATOMIC,
        specific_heat=1.722,
        density=0.1799
    ),
    ChemicalProperties(
        'Ethane', 'C_2H_6',
        molecular_structure=MolecularStructure.POLYATOMIC,
        specific_heat=0.4097,
        density=1.342
    ),
    ChemicalProperties(
        'Fluorine', 'F_2',
        molecular_structure=MolecularStructure.DIATOMIC,
        specific_heat=0.1873,
        density=1.695
    ),
    ChemicalProperties(
        'Helium', 'He',
        molecular_structure=MolecularStructure.MONATOMIC,
        specific_heat=1.241,
        density=0.1786
    ),
    ChemicalProperties(
        'Hexane', 'C_6H14',
        molecular_structure=MolecularStructure.POLYATOMIC,
        specific_heat=0.54,
        density=0.672
    ),
    ChemicalProperties(
        'Hydrogen', 'H_2',
        molecular_structure=MolecularStructure.DIATOMIC,
        specific_heat=3.3852,
        density=0.0899
    ),
    ChemicalProperties(
        'Hydrogen-chloride', 'HCl',
        molecular_structure=MolecularStructure.DIATOMIC,
        specific_heat=0.1912,
        density=1.627
    ),
    ChemicalProperties(
        'Hydrogen-fluoride', 'HF',
        molecular_structure=MolecularStructure.DIATOMIC,
        specific_heat=0.3479,
        density=0.893
    ),
    ChemicalProperties(
        'Methane', 'CH_4',
        molecular_structure=MolecularStructure.POLYATOMIC,
        specific_heat=0.5223,
        density=0.716
    ),
    ChemicalProperties(
        'Neon', 'Ne',
        molecular_structure=MolecularStructure.MONATOMIC,
        specific_heat=0.246,
        density=0.9
    ),
    ChemicalProperties(
        'Nitrogen', 'N_2',
        molecular_structure=MolecularStructure.DIATOMIC,
        specific_heat=0.2485,
        density=1.25,
        inert=True
    ),
    ChemicalProperties(
        'Nitric-oxide', 'NO',
        molecular_structure=MolecularStructure.DIATOMIC,
        specific_heat=0.2328,
        density=1.339
    ),
    ChemicalProperties(
        'Nitric-oxides', 'NO_x'
    ),
    ChemicalProperties(
        'Nitrogen-dioxide', 'NO_2',
        molecular_structure=MolecularStructure.TRIATOMIC,
        specific_heat=0.1933,
        density=2.052
    ),
    ChemicalProperties(
        'Nitrous-oxide', 'N_2O',
        molecular_structure=MolecularStructure.TRIATOMIC,
        specific_heat=0.2088,
        density=1.964
    ),
    ChemicalProperties(
        'Oxygen', 'O_2',
        molecular_structure=MolecularStructure.DIATOMIC,
        specific_heat=0.2193,
        density=1.427
    ),
    ChemicalProperties(
        'Phosphine', 'PH_3',
        molecular_structure=MolecularStructure.POLYATOMIC,
        specific_heat=0.2374,
        density=1.517
    ),
    ChemicalProperties(
        'Propane', 'C_3H_8',
        molecular_structure=MolecularStructure.POLYATOMIC,
        specific_heat=0.3885,
        density=1.967
    ),
    ChemicalProperties(
        'Propylene', 'C_3H_6',
        molecular_structure=MolecularStructure.POLYATOMIC,
        specific_heat=0.3541,
        density=1.877
    ),
    ChemicalProperties(
        'Sulfur Hexaflouride', 'SF_6',
        molecular_structure=MolecularStructure.POLYATOMIC,
        specific_heat=0.1592,
        density=6.516
    ),
    ChemicalProperties(
        'Xenon', 'Xe',
        molecular_structure=MolecularStructure.MONATOMIC,
        specific_heat=0.0378,
        density=5.858
    ),

    ChemicalProperties(
        'Humid Air',
        molecular_structure=MolecularStructure.DIATOMIC,
        specific_heat=0.24,
        density=1.293,
        inert=True,
        humid=True
    ),
    ChemicalProperties(
        'Humid Argon', 'Ar',
        molecular_structure=MolecularStructure.MONATOMIC,
        specific_heat=0.1244,
        density=1.782,
        inert=True,
        humid=True
    ),
    ChemicalProperties(
        'Humid Nitrogen', 'N_2',
        molecular_structure=MolecularStructure.DIATOMIC,
        specific_heat=0.2485,
        density=1.25,
        inert=True,
        humid=True
    )
])


@attr.s(frozen=True)
class Component(object):
    # Actual concentration
    quantity: Union[unit.TYPE_PARSE_VALUE, unit.Quantity] = attr.ib(converter=unit.converter())

    # Gas type
    properties: ChemicalProperties = attr.ib()

    def __attrs_post_init__(self):
        # Check for negative concentrations
        if self.quantity < 0:
            raise NegativeQuantityError('Gas concentration cannot be below zero')

        # Scale concentration to look nice
        magnitude = abs(self.quantity.m_as(unit.dimensionless))

        if magnitude >= 1e-4:
            units = unit.registry.pct
        elif magnitude >= 1e-6:
            units = unit.registry.ppm
        elif magnitude > 0:
            units = unit.registry.ppb
        else:
            units = unit.dimensionless

        object.__setattr__(self, 'quantity', self.quantity.to(units))

    @property
    def gcf(self) -> float:
        return (0.3106 * self.properties.molecular_structure.value /
                (self.properties.density * self.properties.specific_heat)).magnitude

    def __rmul__(self, other):
        return Component(other * self.quantity, self.properties)

    def __str__(self):
        return f"{self.quantity!s} {self.properties!s}"


@attr.s(frozen=True)
class Mixture(object):
    # Gases in mixture
    components: List[Component] = attr.ib()

    # Balance gas
    balance: Component = attr.ib()

    _GAS_CONCENTRATION_PATTERN = re.compile(r'^([\d]+\.?[\d]*)[ ]?([%\w]+) ([\w\s-]+)')

    def __attrs_post_init__(self):
        # Check components and balance do not exceed 100% within a small tolerance (ppt)
        overall_quantity = self.balance.quantity

        for component in self.components:
            overall_quantity += component.quantity

        if (overall_quantity.m_as(unit.dimensionless) - 1) > 1e-12:
            raise CalculationError(f"Gases in mixture sum to over 100% (components: "
                                   f"{', '.join(map(str, self.components))}, balance: {self.balance})")

        # Sort components by concentration
        object.__setattr__(self, 'components', sorted(self.components, key=lambda x: x.quantity, reverse=True))

    @property
    def is_humid(self) -> bool:
        """ True if no component in the gas carries humidity.

        :return:
        """
        return any((component.properties.humid for component in self.components)) or self.balance.properties.humid

    @property
    def humid_ratio(self) -> unit.Quantity:
        ratio = 0.0

        for component in self.components:
            if component.properties.humid:
                ratio += component.quantity

        return unit.Quantity(ratio, unit.dimensionless).to(unit.registry.pct)

    @property
    def is_inert(self) -> bool:
        """ True if all gases in mixture are inert.

        :return:
        """
        return all((component.properties.inert for component in self.components)) and self.balance.properties.inert

    @property
    def gcf(self) -> float:
        """ Gas correction factor used for mass flow control.

        :return: gas correction factor
        """
        components = self.components + [self.balance]

        return (0.3106 * sum((c.quantity * c.properties.molecular_structure.value for c in components)) /
                sum((c.quantity * c.properties.density * c.properties.specific_heat for c in components))).magnitude

    def __str__(self):
        if len(self.components) > 0:
            return f"{', '.join(map(str, self.components))}"
        else:
            return str(self.balance)

    def __mul__(self, other):
        if isinstance(other, int):
            other = float(other)
        elif isinstance(other, unit.Quantity):
            if not other.dimensionless:
                raise CalculationError('Multiplication factor must be dimensionless')

            # Cast to magnitude
            other = other.to(unit.dimensionless).magnitude

        if not isinstance(other, float):
            raise NotImplementedError(f"Cannot multiply {type(other)} by Mixture")

        scaled_gases = [other * gas for gas in self.components]

        return Mixture(scaled_gases, self.balance)

    def __rmul__(self, other):
        return self * other

    def __add__(self, other):
        gas_component_dict = {}

        if isinstance(other, Mixture):
            if self.balance.properties != other.balance.properties:
                raise MixingError(f"Incompatible balance components {self.balance} != {other.balance}")

            for component in self.components + other.components:
                if component.properties in gas_component_dict:
                    gas_component_dict[component.properties] += component.quantity
                else:
                    gas_component_dict[component.properties] = component.quantity

            return Mixture.auto_balance(
                [Component(quantity, properties) for properties, quantity in gas_component_dict.items()],
                self.balance.properties
            )
        elif isinstance(other, Component):
            self.components.append(other)

            return self
        else:
            raise NotImplementedError(f"Cannot add {type(other)} to Mixture")

    def __radd__(self, other):
        return self + other

    @classmethod
    def auto_balance(cls, components: List[Component], balance: ChemicalProperties) -> Mixture:
        # Calculate balance concentration automatically
        balance_quantity = 1.0

        for component in components:
            balance_quantity -= component.quantity

        return Mixture(components, Component(unit.Quantity(balance_quantity, unit.dimensionless), balance))

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
                concentration = unit.Quantity(1, unit.dimensionless)
                gas_name = gas_str

            if gas_name.lower() in registry:
                gas = registry[gas_name.lower()]
            else:
                raise UnknownGas(f"Unknown gas \"{gas_name}\" (from: \"{gas_str}\")")

            gases.append(Component(concentration, gas))

        return cls.auto_balance(gases[:-1], gases[-1].properties)
