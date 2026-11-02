from collections import defaultdict
from datetime import date

from butterfly.infrastructure.memory.companies import COMPANIES, INA1, INA2, INA3
from butterfly.infrastructure.memory.story_seed import build_story_seed

TODAY = date(2026, 10, 31)
GROUP = build_story_seed(TODAY, companies=COMPANIES)
LIVE = [o for o in GROUP.orders if o.overall_status != "X"]


class TestEachCompanyHasItsOwnMasterData:
    def test_the_codes_are_the_three_group_companies(self):
        assert [c.code for c in COMPANIES] == ["INA1", "INA2", "INA3"]

    def test_no_customer_or_material_is_shared(self):
        customers = [c.customer_id for company in COMPANIES for c in company.customers]
        materials = [m[0] for company in COMPANIES for m in company.materials]
        assert len(set(customers)) == len(customers) and len(set(materials)) == len(materials)

    def test_no_company_sells_steel(self):
        names = [m[1] for company in COMPANIES for m in company.materials]
        assert not [n for n in names if "steel" in n.lower() or "bolt" in n.lower() or "bearing" in n.lower()]

    def test_most_customers_are_abroad(self):
        customers = [c for company in COMPANIES for c in company.customers]
        assert sum(c.country != "IN" for c in customers) > len(customers) / 2

    def test_the_usa_is_the_largest_market(self):
        sold = defaultdict(float)
        for order in LIVE:
            if order.transaction_currency == "USD":
                sold[order.country] += float(order.total_net_amount)
        assert max(sold, key=sold.get) == "US"


class TestTheGroupData:
    def test_every_company_has_orders_that_only_use_its_own_customers_and_materials(self):
        for company in COMPANIES:
            customers = {c.customer_id for c in company.customers}
            materials = {m[0] for m in company.materials}
            orders = [o for o in GROUP.orders if o.company_code == company.code]
            assert orders
            assert all(o.sold_to_party in customers and {i.material for i in o.items} <= materials for o in orders)

    def test_both_currencies_are_in_use(self):
        assert {o.transaction_currency for o in GROUP.orders} == {"INR", "USD"}

    def test_a_customer_always_buys_in_one_currency_and_country(self):
        seen = defaultdict(set)
        for order in GROUP.orders:
            seen[order.sold_to_party].add((order.transaction_currency, order.country))
        assert all(len(pairs) == 1 for pairs in seen.values())

    def test_order_numbers_do_not_overlap_between_companies(self):
        numbers = [o.sales_order for o in GROUP.orders]
        assert len(set(numbers)) == len(numbers)

    def test_contracts_are_in_the_currency_of_the_customer(self):
        currencies = {c.customer_id: c.currency for company in COMPANIES for c in company.customers}
        assert all(contract.transaction_currency == currencies[contract.sold_to_party] for contract in GROUP.contracts)

    def test_only_the_story_company_has_scenario_events(self):
        quiet = build_story_seed(TODAY, companies=[INA2, INA3])
        again = build_story_seed(TODAY, find_quiet(), companies=[INA2, INA3])
        assert quiet.orders == again.orders


def find_quiet():
    from butterfly.infrastructure.memory.scenarios import find_scenario
    return find_scenario("quiet-month")


class TestEachCompanyBuysAndMakesItsOwn:
    def test_deliveries_use_only_the_suppliers_and_raw_materials_of_their_company(self):
        for company in COMPANIES:
            suppliers = {s[0] for s in company.suppliers}
            raws = {r[0] for r in company.raw_materials}
            rows = [d for d in GROUP.deliveries if d.company_code == company.code]
            assert rows and all(d.supplier in suppliers and d.material in raws for d in rows)

    def test_no_supplier_or_raw_material_is_shared(self):
        suppliers = [s[0] for company in COMPANIES for s in company.suppliers]
        raws = [r[0] for company in COMPANIES for r in company.raw_materials]
        assert len(set(suppliers)) == len(suppliers) and len(set(raws)) == len(raws)

    def test_production_orders_and_components_follow_the_products_of_their_company(self):
        for company in COMPANIES:
            products = {m[0] for m in company.materials}
            raws = {r[0] for r in company.raw_materials}
            orders = [p for p in GROUP.production_orders if p.company_code == company.code]
            components = [c for c in GROUP.components if c.company_code == company.code]
            assert orders and all(p.material in products for p in orders)
            assert components and all(c.material in raws for c in components)

    def test_every_component_belongs_to_a_production_order_of_the_same_company(self):
        company_of = {p.production_order: p.company_code for p in GROUP.production_orders}
        assert all(company_of[c.production_order] == c.company_code for c in GROUP.components)

    def test_numbers_do_not_overlap_between_companies(self):
        purchase = [d.purchase_order for d in GROUP.deliveries]
        production = [p.production_order for p in GROUP.production_orders]
        assert len(set(purchase)) == len(purchase) and len(set(production)) == len(production)

    def test_imported_raw_material_is_bought_in_dollars_and_local_in_rupees(self):
        assert {d.transaction_currency for d in GROUP.deliveries} == {"INR", "USD"}
        assert {d.transaction_currency for d in GROUP.deliveries if d.company_code == "INA1"} == {"INR"}

    def test_the_story_events_touch_only_the_story_company(self):
        quiet = build_story_seed(TODAY, find_quiet(), companies=[INA2, INA3])
        story = build_story_seed(TODAY, companies=[INA2, INA3])
        assert quiet.deliveries == story.deliveries and quiet.production_orders == story.production_orders
