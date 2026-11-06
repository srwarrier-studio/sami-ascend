from butterfly.application.alpha import external, internal


class TestExternal:
    def test_drops_the_leading_zeros_of_a_number(self):
        assert external("0000100001") == "100001"

    def test_keeps_a_zero_as_a_zero(self):
        assert external("0000000000") == "0"

    def test_leaves_a_value_that_is_not_all_digits(self):
        assert external("USCU-L-200") == "USCU-L-200"
        assert external("0A12") == "0A12"
        assert external("") == ""


class TestInternal:
    def test_pads_a_number_to_ten_digits(self):
        assert internal("100001") == "0000100001"

    def test_leaves_a_number_that_is_already_ten_digits(self):
        assert internal("0000100001") == "0000100001"

    def test_leaves_a_value_that_is_not_all_digits_or_longer_than_ten(self):
        assert internal("USCU-L-200") == "USCU-L-200"
        assert internal("12345678901") == "12345678901"

    def test_comes_back_to_the_shown_form(self):
        assert external(internal("17100001")) == "17100001"
