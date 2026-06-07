from src.common.config import Rules
from src.common.country import CountryResolver


def test_preset_country_codes():
    rules = Rules.load()
    resolver = CountryResolver(rules)
    assert resolver.resolve("Canada") == "CA"
    assert resolver.resolve("United States") == "US"
    assert resolver.resolve("France") == "FR"
    assert resolver.resolve("英国") == "GB"


def test_case_insensitive_country():
    rules = Rules.load()
    resolver = CountryResolver(rules)
    assert resolver.resolve("canada") == "CA"
