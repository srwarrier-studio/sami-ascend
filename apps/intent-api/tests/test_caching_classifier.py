from fakes import FakeClassifier

from intent_api.domain.entities.decision import Decision
from intent_api.infrastructure.caching_classifier import CachingClassifier

CHOICES = {"a": "first", "b": "second"}


class TestCachingClassifier:
    def test_asks_once_for_the_same_text_question_and_choices(self):
        inner = FakeClassifier(Decision("a", 0.8))
        cached = CachingClassifier(inner)
        assert cached.choose("x", "q", CHOICES) == cached.choose("x", "q", CHOICES) == Decision("a", 0.8)
        assert len(inner.calls) == 1

    def test_a_different_text_question_or_choice_list_is_asked_again(self):
        inner = FakeClassifier(Decision("a", 0.8))
        cached = CachingClassifier(inner)
        cached.choose("x", "q", CHOICES)
        cached.choose("y", "q", CHOICES)
        cached.choose("x", "other", CHOICES)
        cached.choose("x", "q", {"b": "second", "a": "first"})
        assert len(inner.calls) == 4
