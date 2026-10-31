import pytest

from sami_agents.application.reply_sentence import accept_sentence

TITLES = ["Top customers", "Top materials"]


class TestAccepted:
    def test_a_clean_sentence_naming_a_widget_is_accepted(self):
        assert accept_sentence("Let's review the top customers for you.", TITLES) == "Let's review the top customers for you."

    def test_surrounding_space_and_quotes_are_removed(self):
        assert accept_sentence('  "Showing the Top materials now."  ', TITLES) == "Showing the Top materials now."

    def test_the_title_match_ignores_case(self):
        assert accept_sentence("Here are the TOP CUSTOMERS today.", TITLES) is not None

    def test_without_titles_the_widget_check_is_skipped(self):
        assert accept_sentence("Here you go my friend.") == "Here you go my friend."


class TestRejected:
    @pytest.mark.parametrize("text", ["", "   ", "\n"])
    def test_empty_text(self, text):
        assert accept_sentence(text, TITLES) is None

    def test_more_than_one_line(self):
        assert accept_sentence("Showing top customers.\nAnd more text here.", TITLES) is None

    def test_too_long(self):
        assert accept_sentence("Showing top customers " + "and more " * 30, TITLES) is None

    def test_too_short_to_be_a_sentence(self):
        assert accept_sentence("Top customers", TITLES) is None
        assert accept_sentence("Top customers, Top materials", TITLES) is None

    @pytest.mark.parametrize("text", ["Showing <b>top customers</b> now.", "Showing `top customers` for you.", "Showing **top customers** for you.", "# Showing top customers for you", "Showing [top customers](x) for you.", "Showing top customers for {you}."])
    def test_markup_and_markdown(self, text):
        assert accept_sentence(text, TITLES) is None

    @pytest.mark.parametrize("text", ["Showing the top 5 customers for you.", "Showing top customers, up 12 percent."])
    def test_numbers_the_model_could_have_made_up(self, text):
        assert accept_sentence(text, TITLES) is None

    @pytest.mark.parametrize("text", ["See top customers at https://evil.example now.", "See top customers at www.evil.example now."])
    def test_links(self, text):
        assert accept_sentence(text, TITLES) is None

    def test_a_sentence_that_names_none_of_the_widgets(self):
        assert accept_sentence("Okay, I am ready to be your dashboard!", TITLES) is None
