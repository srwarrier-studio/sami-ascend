from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from butterfly.domain.entities.master_data import in_currency


@dataclass(frozen=True)
class GroupCustomer:
    customer_id: str
    name: str
    country: str
    currency: str
    terms_days: int
    delay_days: int


@dataclass(frozen=True)
class CompanyProfile:
    code: str
    name: str
    customers: list[GroupCustomer]
    materials: list[tuple]
    quantity_factor: list[Decimal]
    contracts: list[list[tuple]]
    first_order_number: int
    suppliers: list[tuple]
    raw_materials: list[tuple]
    ordered_quantity: list[Decimal]
    planned_quantity: list[Decimal]
    raw_price: list[Decimal]
    purchase_order_base: int
    production_order_base: int


def decimals(*values: str) -> list[Decimal]:
    return [Decimal(value) for value in values]


INA1 = CompanyProfile(
    code="INA1",
    name="Sami-Sabinsa Group Limited",
    customers=[
        GroupCustomer("0000100001", "Harborline Nutrition LLC", "US", "USD", 30, 0),
        GroupCustomer("0000100002", "Eurovita Ingredients GmbH", "DE", "USD", 45, 20),
        GroupCustomer("0000100003", "Nordic Botanicals AB", "SE", "USD", 60, 75),
        GroupCustomer("0000100004", "Pacific Wellness Pty Ltd", "AU", "USD", 30, 10),
        GroupCustomer("0000100005", "Lakeshore Supplements Inc", "US", "USD", 45, 1000),
    ],
    materials=[
        ("RM-1001", "Curcumin extract 95%", "KG", Decimal("1250.00")),
        ("RM-1002", "Piperine extract 95%", "KG", Decimal("2500.00")),
        ("RM-1003", "Boswellia extract 65%", "KG", Decimal("840.00")),
        ("RM-1004", "Ashwagandha extract 2.5%", "KG", Decimal("610.50")),
        ("RM-1005", "Probiotic capsule 10B CFU", "EA", Decimal("95.00")),
        ("RM-1006", "Herbal stick pack 5g", "EA", Decimal("4.25")),
    ],
    quantity_factor=decimals("1", "0.5", "1.5", "2", "12", "250"),
    contracts=[
        [("0040000071", None, date(2024, 7, 13), date(2025, 7, 12), "8000000.00"), ("0040000127", "0040000071", date(2025, 7, 13), date(2026, 7, 12), "9000000.00"), ("0040000163", "0040000127", date(2026, 7, 13), date(2027, 7, 12), "10000000.00")],
        [("0040000101", None, date(2025, 4, 1), date(2026, 3, 31), "6000000.00"), ("0040000150", "0040000101", date(2026, 4, 1), date(2027, 3, 31), "6500000.00")],
        [("0040000102", None, date(2025, 1, 1), date(2025, 12, 31), "5000000.00"), ("0040000151", "0040000102", date(2026, 1, 1), date(2026, 12, 31), "5500000.00")],
        [("0040000103", None, date(2024, 10, 1), date(2025, 9, 30), "4200000.00"), ("0040000152", "0040000103", date(2025, 10, 1), date(2026, 9, 30), "4500000.00"), ("0040000160", "0040000152", date(2026, 10, 1), date(2027, 9, 30), "4800000.00")],
        [("0040000104", None, date(2025, 1, 15), date(2026, 1, 14), "5000000.00"), ("0040000153", "0040000104", date(2026, 1, 15), date(2027, 1, 14), "5200000.00")],
    ],
    first_order_number=20001,
    suppliers=[
        ("0000200001", "Deccan Agro Growers Cooperative"),
        ("0000200002", "Malnad Botanicals Pvt Ltd"),
        ("0000200003", "Pack-Rite Industries Pvt Ltd"),
    ],
    raw_materials=[
        ("RAW-2001", "Turmeric rhizome, dried", "KG", 0, "RM-1001", "INR"),
        ("RAW-2002", "Black pepper, whole", "KG", 0, "RM-1002", "INR"),
        ("RAW-2003", "Frankincense resin", "KG", 1, "RM-1003", "INR"),
        ("RAW-2004", "Withania root, dried", "KG", 1, "RM-1004", "INR"),
        ("RAW-2005", "Gelatin capsule shells", "KG", 2, "RM-1005", "INR"),
        ("RAW-2006", "Laminate film for sachets", "KG", 2, "RM-1006", "INR"),
    ],
    ordered_quantity=decimals("4000.000", "5000.000", "2000.000", "1500.000", "1000.000", "3000.000"),
    planned_quantity=decimals("3500.000", "4000.000", "1800.000", "1400.000", "900.000", "2800.000"),
    raw_price=decimals("46.00", "52.00", "610.00", "190.00", "70.00", "48.00"),
    purchase_order_base=4500001146,
    production_order_base=1000356,
)

INA2 = CompanyProfile(
    code="INA2",
    name="Sami Nutraceuticals Private Limited",
    customers=[
        GroupCustomer("0000110001", "Summit Health Brands Inc", "US", "USD", 45, 5),
        GroupCustomer("0000110002", "Vitalis Pharma BV", "NL", "USD", 60, 30),
        GroupCustomer("0000110003", "Maple Leaf Naturals Ltd", "CA", "USD", 45, 15),
        GroupCustomer("0000110004", "Sanjeevani Wellness Pvt Ltd", "IN", "INR", 30, 10),
        GroupCustomer("0000110005", "Kaveri Nutrition Distributors", "IN", "INR", 30, 40),
    ],
    materials=[
        ("NU-1001", "Probiotic blend 50B CFU", "KG", Decimal("3200.00")),
        ("NU-1002", "Lactobacillus acidophilus powder", "KG", Decimal("2100.00")),
        ("NU-1003", "Bifidobacterium longum powder", "KG", Decimal("2400.00")),
        ("NU-1004", "Turmeric complex softgel 500mg", "EA", Decimal("14.00")),
        ("NU-1005", "Immune support capsule", "EA", Decimal("8.50")),
        ("NU-1006", "Joint care tablet", "EA", Decimal("6.00")),
    ],
    quantity_factor=decimals("1", "1.2", "1", "40", "60", "80"),
    contracts=[
        [("0050000011", None, date(2025, 3, 1), date(2026, 2, 28), "4000000.00"), ("0050000041", "0050000011", date(2026, 3, 1), date(2027, 2, 28), "4400000.00")],
        [("0050000012", None, date(2025, 6, 1), date(2026, 5, 31), "3000000.00"), ("0050000042", "0050000012", date(2026, 6, 1), date(2027, 5, 31), "3300000.00")],
        [("0050000013", None, date(2025, 9, 1), date(2026, 8, 31), "2600000.00"), ("0050000043", "0050000013", date(2026, 9, 1), date(2027, 8, 31), "2800000.00")],
        [("0050000014", None, date(2025, 1, 1), date(2025, 12, 31), "1800000.00"), ("0050000044", "0050000014", date(2026, 1, 1), date(2026, 12, 31), "2000000.00")],
        [("0050000015", None, date(2025, 4, 1), date(2026, 3, 31), "1500000.00"), ("0050000045", "0050000015", date(2026, 4, 1), date(2027, 3, 31), "1600000.00")],
    ],
    first_order_number=30001,
    suppliers=[
        ("0000210001", "Nordic Cultures ApS"),
        ("0000210002", "Malnad Extracts Pvt Ltd"),
        ("0000210003", "Qingdao Bioactives Co Ltd"),
    ],
    raw_materials=[
        ("NRAW-2001", "Probiotic culture concentrate", "KG", 0, "NU-1001", "USD"),
        ("NRAW-2002", "Lactobacillus culture, freeze-dried", "KG", 0, "NU-1002", "USD"),
        ("NRAW-2003", "Bifidobacterium culture, freeze-dried", "KG", 0, "NU-1003", "USD"),
        ("NRAW-2004", "Turmeric extract, bulk", "KG", 1, "NU-1004", "INR"),
        ("NRAW-2005", "Vitamin C and zinc premix", "KG", 1, "NU-1005", "INR"),
        ("NRAW-2006", "Glucosamine sulphate", "KG", 2, "NU-1006", "USD"),
    ],
    ordered_quantity=decimals("900.000", "700.000", "650.000", "3200.000", "2500.000", "2100.000"),
    planned_quantity=decimals("800.000", "620.000", "600.000", "3000.000", "2300.000", "1900.000"),
    raw_price=decimals("2600.00", "1700.00", "1900.00", "850.00", "420.00", "380.00"),
    purchase_order_base=4600001000,
    production_order_base=2000356,
)

INA3 = CompanyProfile(
    code="INA3",
    name="Organica Aromatics Private Limited",
    customers=[
        GroupCustomer("0000120001", "Aromatix Flavors Corp", "US", "USD", 30, 10),
        GroupCustomer("0000120002", "Fragrance Atelier SA", "FR", "USD", 60, 25),
        GroupCustomer("0000120003", "Gulf Aroma Trading LLC", "AE", "USD", 45, 60),
        GroupCustomer("0000120004", "Bengaluru Essences Pvt Ltd", "IN", "INR", 30, 5),
        GroupCustomer("0000120005", "Tokyo Scent Labs KK", "JP", "USD", 60, 20),
    ],
    materials=[
        ("OA-1001", "Vanillin crystals", "KG", Decimal("1500.00")),
        ("OA-1002", "Menthol crystals", "KG", Decimal("2200.00")),
        ("OA-1003", "Eugenol", "KG", Decimal("950.00")),
        ("OA-1004", "Citral", "KG", Decimal("1100.00")),
        ("OA-1005", "Linalool", "KG", Decimal("1300.00")),
        ("OA-1006", "Ethyl maltol", "KG", Decimal("1800.00")),
    ],
    quantity_factor=decimals("1", "0.8", "1.5", "1.2", "1.4", "0.6"),
    contracts=[
        [("0060000021", None, date(2025, 2, 1), date(2026, 1, 31), "5000000.00"), ("0060000051", "0060000021", date(2026, 2, 1), date(2027, 1, 31), "5500000.00")],
        [("0060000022", None, date(2025, 5, 1), date(2026, 4, 30), "4200000.00"), ("0060000052", "0060000022", date(2026, 5, 1), date(2027, 4, 30), "4600000.00")],
        [("0060000023", None, date(2025, 8, 1), date(2026, 7, 31), "3600000.00"), ("0060000053", "0060000023", date(2026, 8, 1), date(2027, 7, 31), "3900000.00")],
        [("0060000024", None, date(2025, 1, 1), date(2025, 12, 31), "2400000.00"), ("0060000054", "0060000024", date(2026, 1, 1), date(2026, 12, 31), "2600000.00")],
        [("0060000025", None, date(2025, 10, 1), date(2026, 9, 30), "3000000.00"), ("0060000055", "0060000025", date(2026, 10, 1), date(2027, 9, 30), "3200000.00")],
    ],
    first_order_number=40001,
    suppliers=[
        ("0000220001", "Mysore Oils and Terpenes Pvt Ltd"),
        ("0000220002", "Kannur Essential Oils Co"),
        ("0000220003", "Jiangsu Aroma Intermediates Co Ltd"),
    ],
    raw_materials=[
        ("ORAW-2001", "Guaiacol", "KG", 2, "OA-1001", "USD"),
        ("ORAW-2002", "Mentha arvensis oil, crude", "KG", 0, "OA-1002", "INR"),
        ("ORAW-2003", "Clove leaf oil", "KG", 1, "OA-1003", "INR"),
        ("ORAW-2004", "Lemongrass oil", "KG", 1, "OA-1004", "INR"),
        ("ORAW-2005", "Linalool, crude", "KG", 0, "OA-1005", "INR"),
        ("ORAW-2006", "Maltol precursor", "KG", 2, "OA-1006", "USD"),
    ],
    ordered_quantity=decimals("3500.000", "4500.000", "2800.000", "2400.000", "2600.000", "1200.000"),
    planned_quantity=decimals("3200.000", "4100.000", "2600.000", "2200.000", "2400.000", "1100.000"),
    raw_price=decimals("900.00", "1400.00", "620.00", "700.00", "800.00", "1100.00"),
    purchase_order_base=4700001000,
    production_order_base=3000356,
)

COMPANIES = [INA1, INA2, INA3]
