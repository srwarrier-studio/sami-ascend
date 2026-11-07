from datetime import date, datetime

from dateparser.date import DateDataParser
from dateparser.search import search_dates

from intent_api.domain.gateways.fallback_periods import FallbackPeriods, FoundDate

MIN_LETTERS = 3


class DateparserPeriods(FallbackPeriods):
    def find(self, text: str, today: date) -> list[FoundDate]:
        settings = {"RELATIVE_BASE": datetime(today.year, today.month, today.day), "PREFER_DATES_FROM": "past"}
        hits = search_dates(text, languages=["en"], settings=settings) or []
        parser = DateDataParser(languages=["en"], settings=settings)
        found = []
        for phrase, moment in hits:
            if sum(char.isalpha() for char in phrase) < MIN_LETTERS and not any(char.isdigit() for char in phrase):
                continue
            data = parser.get_date_data(phrase)
            found.append(FoundDate(phrase, data["period"], moment.date()))
        return found
