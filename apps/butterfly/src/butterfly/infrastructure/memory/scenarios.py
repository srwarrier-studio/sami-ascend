from datetime import date

from butterfly.domain.entities.scenario import (
    Cancellations,
    ContractEnd,
    CustomerLoss,
    DemandGrowth,
    Drop,
    PriceChange,
    ProductionDelay,
    PurchasePriceChange,
    PurchaseQuantityChange,
    Scenario,
    SupplierSwitch,
    SupplyDelay,
)

HARBORLINE, EUROVITA, NORDIC, PACIFIC, LAKESHORE = range(5)

CURCUMIN = "RM-1001"
PIPERINE = "RM-1002"
BOSWELLIA = "RM-1003"
PROBIOTIC_CAPSULE = "RM-1005"
BLACK_PEPPER = "RAW-2002"
FRANKINCENSE = "RAW-2003"
WITHANIA_ROOT = "RAW-2004"
CAPSULE_SHELLS = "RAW-2005"
LAMINATE_FILM = "RAW-2006"
MALNAD = 1

JULY = date(2026, 7, 1)
MAY = date(2026, 5, 1)

PIPERINE_DELAYS = (
    SupplyDelay(BLACK_PEPPER, JULY, 12, Drop(PIPERINE, date(2026, 7, 20), date(2026, 8, 31), 3, 5)),
    ProductionDelay(PIPERINE, JULY, 14, "MATERIAL_SHORTAGE"),
)

MAY_DECOYS = (
    SupplyDelay(FRANKINCENSE, MAY, 4),
    ProductionDelay(PROBIOTIC_CAPSULE, MAY, 6, "MACHINE_BREAKDOWN"),
)

AUGUST_CONTRACT = Scenario(
    "august-contract",
    (
        ContractEnd(HARBORLINE, date(2026, 7, 12), date(2026, 9, 14), "0040000163", spot=True),
        *PIPERINE_DELAYS,
        *MAY_DECOYS,
    ),
)

SCENARIOS = [
    AUGUST_CONTRACT,
    Scenario("price-cut", (PriceChange(CURCUMIN, "0.85", date(2026, 8, 1)),)),
    Scenario(
        "supplier-no-effect",
        (
            SupplyDelay(BLACK_PEPPER, JULY, 12),
            ProductionDelay(PIPERINE, JULY, 14, "MATERIAL_SHORTAGE"),
        ),
    ),
    Scenario("customer-lost", (CustomerLoss(LAKESHORE, date(2026, 8, 10)),)),
    Scenario(
        "breakdown-shortfall",
        (ProductionDelay(PROBIOTIC_CAPSULE, JULY, 10, "MACHINE_BREAKDOWN", Drop(PROBIOTIC_CAPSULE, date(2026, 7, 20), date(2026, 8, 15), 1, 2, (EUROVITA, NORDIC, PACIFIC))),),
    ),
    Scenario("quiet-month", ()),
    Scenario(
        "two-causes",
        (
            ContractEnd(PACIFIC, date(2026, 7, 20)),
            SupplyDelay(FRANKINCENSE, JULY, 10, Drop(BOSWELLIA, date(2026, 7, 20), date(2026, 8, 31), 1, 2, (HARBORLINE, EUROVITA, NORDIC, LAKESHORE))),
        ),
        holdout=True,
    ),
    Scenario(
        "cancellations",
        (Cancellations(NORDIC, 2, 5, date(2026, 8, 1), date(2026, 8, 31)),),
        holdout=True,
    ),
    Scenario("purchase-price-rise", (PurchasePriceChange(BLACK_PEPPER, "1.2", date(2026, 8, 1)),)),
    Scenario("stock-up", (PurchaseQuantityChange(FRANKINCENSE, "1.6", date(2026, 9, 1), date(2026, 9, 30)),)),
    Scenario("demand-surge", (DemandGrowth(PIPERINE, "1.35", date(2026, 6, 15)),)),
    Scenario("quiet-purchases", ()),
    Scenario("supplier-switch", (SupplierSwitch(CAPSULE_SHELLS, MALNAD, "1.15", date(2026, 10, 1)),), holdout=True),
    Scenario(
        "double-cause",
        (
            PurchasePriceChange(WITHANIA_ROOT, "1.25", date(2026, 9, 1)),
            PurchaseQuantityChange(LAMINATE_FILM, "1.5", date(2026, 9, 1), date(2026, 9, 30)),
        ),
        holdout=True,
    ),
]


def find_scenario(name: str) -> Scenario:
    for scenario in SCENARIOS:
        if scenario.name == name:
            return scenario
    names = ", ".join(s.name for s in SCENARIOS)
    raise SystemExit(f"BUTTERFLY_SCENARIO must be one of {names}, not '{name}'")
