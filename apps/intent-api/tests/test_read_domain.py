import pytest
from fakes import FakeClassifier

from intent_api.application.read_domain import OTHER, QUESTION, ReadDomain
from intent_api.domain.entities.decision import Decision
from intent_api.domain.errors import ClassifierUnavailable

DOMAINS = {"Sales": "sales orders, revenue", "Purchase": "purchases, spend"}


class TestReadDomain:
    def test_offers_every_domain_and_other_with_the_question(self):
        classifier = FakeClassifier(Decision("Sales", 0.9))
        ReadDomain(classifier, DOMAINS).execute("sales in august")
        assert classifier.calls == [("sales in august", QUESTION, {**DOMAINS, OTHER: "everything else"})]

    def test_returns_the_domain_with_its_probability(self):
        assert ReadDomain(FakeClassifier(Decision("Purchase", 0.7)), DOMAINS).execute("spend") == Decision("Purchase", 0.7)

    def test_other_is_returned_as_it_is(self):
        assert ReadDomain(FakeClassifier(Decision(OTHER, 0.6)), DOMAINS).execute("joke").choice == OTHER

    def test_laya_down_is_not_swallowed(self):
        with pytest.raises(ClassifierUnavailable):
            ReadDomain(FakeClassifier(), DOMAINS).execute("sales")
