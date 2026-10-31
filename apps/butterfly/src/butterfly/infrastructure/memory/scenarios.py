from datetime import date

from butterfly.domain.entities.scenario import (
    Cancellations,
    ContractEnd,
    CustomerLoss,
    Drop,
    PriceChange,
    ProductionDelay,
    Scenario,
    SupplyDelay,
)

ACME, BHARAT, CAUVERY, DECCAN, EASTERN = range(5)

STEEL_ROD = "RM-1001"
STEEL_PLATE = "RM-1002"
COPPER_WIRE = "RM-1003"
BEARING = "RM-1005"
STEEL_COIL = "RAW-2002"
COPPER_ROD = "RAW-2003"

JULY = date(2026, 7, 1)
MAY = date(2026, 5, 1)

STEEL_PLATE_DELAYS = (
    SupplyDelay(STEEL_COIL, JULY, 12, Drop(STEEL_PLATE, date(2026, 7, 20), date(2026, 8, 31), 3, 5)),
    ProductionDelay(STEEL_PLATE, JULY, 14, "MATERIAL_SHORTAGE"),
)

MAY_DECOYS = (
    SupplyDelay(COPPER_ROD, MAY, 4),
    ProductionDelay(BEARING, MAY, 6, "MACHINE_BREAKDOWN"),
)

AUGUST_CONTRACT = Scenario(
    "august-contract",
    (
        ContractEnd(ACME, date(2026, 7, 12), date(2026, 9, 14), "0040000163", spot=True),
        *STEEL_PLATE_DELAYS,
        *MAY_DECOYS,
    ),
)

SCENARIOS = [
    AUGUST_CONTRACT,
    Scenario("price-cut", (PriceChange(STEEL_ROD, "0.85", date(2026, 8, 1)),)),
    Scenario(
        "supplier-no-effect",
        (
            SupplyDelay(STEEL_COIL, JULY, 12),
            ProductionDelay(STEEL_PLATE, JULY, 14, "MATERIAL_SHORTAGE"),
        ),
    ),
    Scenario("customer-lost", (CustomerLoss(EASTERN, date(2026, 8, 10)),)),
    Scenario(
        "breakdown-shortfall",
        (ProductionDelay(BEARING, JULY, 10, "MACHINE_BREAKDOWN", Drop(BEARING, date(2026, 7, 20), date(2026, 8, 15), 1, 2, (BHARAT, CAUVERY, DECCAN))),),
    ),
    Scenario("quiet-month", ()),
    Scenario(
        "two-causes",
        (
            ContractEnd(DECCAN, date(2026, 7, 20)),
            SupplyDelay(COPPER_ROD, JULY, 10, Drop(COPPER_WIRE, date(2026, 7, 20), date(2026, 8, 31), 1, 2, (ACME, BHARAT, CAUVERY, EASTERN))),
        ),
        holdout=True,
    ),
    Scenario(
        "cancellations",
        (Cancellations(CAUVERY, 2, 5, date(2026, 8, 1), date(2026, 8, 31)),),
        holdout=True,
    ),
]


def find_scenario(name: str) -> Scenario:
    for scenario in SCENARIOS:
        if scenario.name == name:
            return scenario
    names = ", ".join(s.name for s in SCENARIOS)
    raise SystemExit(f"BUTTERFLY_SCENARIO must be one of {names}, not '{name}'")
