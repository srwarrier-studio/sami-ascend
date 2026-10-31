import random
import re
from datetime import date, timedelta
from decimal import Decimal

from sami_agents.application import wording
from sami_agents.domain.entities.analysis import Analysis, Cause, Finding
from sami_agents.domain.entities.finding import Step, Window
from sami_agents.domain.entities.question import Question

WINDOW = Window(date(2026, 8, 1), date(2026, 8, 31), date(2026, 7, 1), date(2026, 7, 31))


def analysis(**changes):
    values = dict(question=Question("sales", "fall", date(2026, 8, 1)), window=WINDOW, currency="INR", current=Decimal("6480000"), previous=Decimal("7570000"),
                  change=Decimal("-1090000"), change_percent=Decimal("-14.40"), significant=True)
    values.update(changes)
    return Analysis(**values)


def finding(**changes):
    values = dict(dimension="customer", key="A", name="Acme Industries", current=Decimal("100000"), previous=Decimal("900000"), change=Decimal("-800000"),
                  change_percent=Decimal("-88.89"), share_percent=Decimal("73.4"), kind="volume")
    values.update(changes)
    return Finding(**values)


def step(kind, **numbers):
    return Step("Contract", "customer_contracts", "SoldToParty", ("A",), kind, None, numbers, [])


class TestHeadline:
    def test_a_significant_fall_says_how_much_and_between_which_months(self):
        assert wording.headline(analysis()) == "Sales fell 14.4% from July 2026 to August 2026 (INR 7,570,000 to INR 6,480,000)."

    def test_a_rise(self):
        text = wording.headline(analysis(question=Question("purchases", "rise", date(2026, 9, 1)), window=Window(date(2026, 9, 1), date(2026, 9, 30), date(2026, 8, 1), date(2026, 8, 31)), change=Decimal(5), change_percent=Decimal("33.80"), previous=Decimal(15), current=Decimal(20)))
        assert text == "Purchases rose 33.8% from August 2026 to September 2026 (INR 15 to INR 20)."

    def test_a_small_change_is_called_steady(self):
        text = wording.headline(analysis(significant=False, change=Decimal(-100), change_percent=Decimal("-1.00")))
        assert text.startswith("Sales were steady: they fell 1.0% from July 2026 to August 2026")

    def test_a_month_after_nothing_has_no_percent(self):
        assert wording.headline(analysis(change_percent=None, previous=Decimal(0))) == "Sales were INR 6,480,000 in August 2026 and nothing in July 2026."

    def test_no_data_gives_the_limit_text(self):
        assert wording.headline(analysis(currency="", limits=["There is no data for this metric in these months."])) == "There is no data for this metric in these months."


class TestFindings:
    def test_a_finding_says_name_percent_amount_and_share(self):
        assert wording.finding_sentence(analysis(), finding()) == "Acme Industries fell 88.9% (INR 800,000), 73.4% of the change."

    def test_a_price_finding_adds_the_effects(self):
        f = finding(kind="price", price_effect=Decimal("-700000"), volume_effect=Decimal("-100000"))
        assert wording.finding_sentence(analysis(), f).endswith("Mostly price: the price effect is INR 700,000 and the volume effect INR 100,000.")

    def test_an_offset_says_it_offset_part_of_the_change(self):
        f = finding(name="Bharat Steels", change=Decimal(5000), change_percent=Decimal("5.00"))
        assert wording.offset_sentence(analysis(), f) == "Bharat Steels offset part of it: rose 5.0% (INR 5,000)."


class TestSteps:
    def test_a_coverage_gap_names_the_days_the_date_and_the_document(self):
        text = wording.step_sentence(step("coverage_gap", days_uncovered=50, first_uncovered=date(2026, 7, 13)), "0040000127")
        assert text == "no valid Contract for 50 days from 2026-07-13 (Contract 0040000127)"

    def test_a_late_step_with_and_without_a_reason_and_when_still_open(self):
        numbers = dict(days_late=14, open=False, due=date(2026, 7, 20), done=date(2026, 8, 3), reason="MATERIAL_SHORTAGE")
        assert wording.step_sentence(step("later_than", **numbers), "0001000417") == "Contract 0001000417 was 14 days late (due 2026-07-20, done 2026-08-03, reason MATERIAL_SHORTAGE)"
        assert "reason" not in wording.step_sentence(step("later_than", **{**numbers, "reason": None}), "X")
        assert "still open" in wording.step_sentence(step("later_than", **{**numbers, "open": True, "done": None}), "X")

    def test_a_sum_and_a_set_and_a_value_step(self):
        assert wording.step_sentence(step("sum_changed", previous=Decimal("15000"), current=Decimal("16750"), change_percent=Decimal("11.67")), "k") == "Contract totals went from 15,000 to 16,750 (11.7%)"
        assert wording.step_sentence(step("set_changed", field="Supplier", new=["S2"], gone=["S1"]), "k") == "the Supplier values of Contract changed: new S2; gone S1"
        assert wording.step_sentence(step("value_changed", previous=Decimal(100), current=Decimal(120), change_percent=Decimal("20.00")), "RM-1002") == "Contract RM-1002 rose 20.0%"

    def test_a_chain_is_told_with_behind_that_and_never_with_caused(self):
        causes = [Cause("record:production_order", "later_than", "O1"), Cause("record:purchase_delivery", "later_than", "P1")]
        late = dict(days_late=14, open=False, due=date(2026, 7, 20), done=date(2026, 8, 3), reason=None)
        f = finding(causes=causes, paths=[(step("later_than", **late), step("later_than", **{**late, "days_late": 12}))])
        text = wording.path_sentence(f, 0)
        assert text.startswith("This coincided with Contract O1 was 14 days late") and ", and behind that Contract P1 was 12 days late" in text
        assert "caused" not in text


class TestTheClosingLines:
    def test_the_explained_and_unexplained_shares(self):
        a = analysis(explained_percent=Decimal(70), unexplained_percent=Decimal(30), findings=[finding()])
        assert wording.unexplained_sentence(a) == "At least 70% of the change is explained by what is listed above; 30% is not explained by anything in the data we hold."

    def test_nothing_explained_says_no_cause_was_found(self):
        assert wording.unexplained_sentence(analysis(findings=[finding()])) == "No cause was found in the data we hold."

    def test_a_steady_month_with_no_findings(self):
        assert wording.unexplained_sentence(analysis(significant=False)) == "Nothing unusual was found behind this month."

    def test_lines_run_headline_findings_paths_offsets_the_rest_and_limits(self):
        f = finding(causes=[Cause("record:contract", "coverage_gap", "C1")], paths=[(step("coverage_gap", days_uncovered=5, first_uncovered=date(2026, 8, 1)),)], explained=True)
        a = analysis(findings=[f], offsets=[finding(name="Other Co", change=Decimal(10), change_percent=Decimal(1))], explained_percent=Decimal(70), unexplained_percent=Decimal(30), limits=["Only INR was analysed; there are other currencies."])
        out = wording.lines(a)
        assert [out[0][:10], out[1][:12], out[2][:13], out[3][:8], out[4][:8], out[-1][:4]] == ["Sales fell", "Acme Industr", "This coincide", "Other Co", "At least", "Only"]


def numbers_in(text: str) -> list[str]:
    return re.findall(r"(?<![A-Za-z0-9_])(?:\d{4}-\d{2}-\d{2}|\d[\d,]*(?:\.\d+)?)(?![A-Za-z_])", text)


class TestEveryFigureComesFromTheAnalysis:
    def random_analysis(self, rng: random.Random) -> Analysis:
        def money():
            return Decimal(rng.randint(1, 99_999_999)) / rng.choice([1, 100])

        def pct():
            return Decimal(rng.randint(-9999, 9999)) / 100

        base = date(2026, 1, 1) + timedelta(days=rng.randint(0, 200))
        findings = []
        for n in range(rng.randint(0, 3)):
            kind = rng.choice(["coverage_gap", "later_than", "sum_changed", "set_changed", "value_changed"])
            numbers = {
                "coverage_gap": dict(days_uncovered=rng.randint(1, 170), first_uncovered=base),
                "later_than": dict(days_late=rng.randint(3, 90), open=rng.random() < 0.3, due=base, done=base + timedelta(days=rng.randint(3, 90)), reason=rng.choice([None, "MACHINE_BREAKDOWN"])),
                "sum_changed": dict(current=money(), previous=money(), change_percent=pct()),
                "set_changed": dict(field="Supplier", new=[f"S{rng.randint(1, 9)}"], gone=[]),
                "value_changed": dict(current=money(), previous=money(), change_percent=pct()),
            }[kind]
            key = f"K{rng.randint(100, 999)}"
            f = finding(name=f"Name{chr(65 + n)} Ltd", change=money() * rng.choice([-1, 1]), change_percent=pct(), share_percent=pct(), key=key,
                        kind=rng.choice(["volume", "price"]), price_effect=money(), volume_effect=money())
            f.causes = [Cause("record:x", kind, key)]
            f.paths = [(Step("Contract", None, "k", (key,), kind, base, numbers, []),)]
            findings.append(f)
        total = money()
        return analysis(current=total, previous=money(), change=money() * rng.choice([-1, 1]), change_percent=pct(), significant=rng.random() < 0.7,
                        findings=findings, offsets=[], explained_percent=Decimal(rng.randint(0, 100)), unexplained_percent=Decimal(rng.randint(0, 100)))

    def allowed_numbers(self, a: Analysis) -> set[Decimal]:
        raw: list = [a.current, a.previous, a.change, a.change_percent, a.explained_percent, a.unexplained_percent]
        dates, names = set(), set()
        for f in a.findings:
            raw += [f.change, f.change_percent, f.share_percent, f.price_effect, f.volume_effect]
            for path in f.paths:
                for s in path:
                    for k, v in s.numbers.items():
                        if isinstance(v, date):
                            dates.add(v.isoformat())
                        elif isinstance(v, (int, Decimal)) and not isinstance(v, bool):
                            raw.append(v)
        allowed = set()
        for v in raw:
            if v is None:
                continue
            v = abs(Decimal(v))
            allowed |= {v, v.quantize(Decimal("0.1")), v.quantize(Decimal("1")), v.quantize(Decimal("0.01"))}
        return allowed, dates

    def test_every_number_date_and_name_in_every_sentence_is_in_the_analysis(self):
        rng = random.Random(7)
        for _ in range(200):
            a = self.random_analysis(rng)
            allowed, dates = self.allowed_numbers(a)
            allowed_dates = dates | {"2026-08-01", "2026-07-01"}
            names = {f.name for f in a.findings} | {f.key for f in a.findings}
            for sentence in wording.lines(a):
                for token in numbers_in(sentence):
                    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", token):
                        assert token in allowed_dates, (token, sentence)
                    elif token == "2026":
                        continue
                    else:
                        assert Decimal(token.replace(",", "")) in allowed, (token, sentence)
                for word in re.findall(r"\b[A-Z][\w-]*\b", sentence):
                    known = names | {"Sales", "July", "August", "INR", "Contract", "At", "No", "Nothing", "This", "Mostly", "Supplier", "MACHINE_BREAKDOWN", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"}
                    assert word in known or word in " ".join(names), (word, sentence)
