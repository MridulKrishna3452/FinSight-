import pytest

from app.models.enums import CategorizationSource, Category
from app.services.categorization_service import categorize


@pytest.mark.parametrize(
    "merchant,expected_category",
    [
        ("Swiggy", Category.DINING),
        ("Zomato Order", Category.DINING),
        ("Uber Trip", Category.TRANSPORT),
        ("Ola Cabs", Category.TRANSPORT),
        ("Amazon.in", Category.SHOPPING),
        ("Flipkart", Category.SHOPPING),
        ("Netflix", Category.ENTERTAINMENT),
        ("Spotify Premium", Category.ENTERTAINMENT),
        ("Landlord - Rent", Category.HOUSING),
        ("Airtel Postpaid", Category.UTILITIES),
        ("Jio Fiber", Category.UTILITIES),
        ("BigBasket", Category.GROCERIES),
        ("Apollo Pharmacy", Category.HEALTHCARE),
        ("Zerodha", Category.INVESTMENTS),
    ],
)
def test_merchant_rule_matches(merchant: str, expected_category: Category) -> None:
    result = categorize(merchant, f"{merchant} purchase")
    assert result.category == expected_category
    assert result.source == CategorizationSource.RULE


def test_description_fallback_when_merchant_unknown() -> None:
    result = categorize("Some Random Business", "paid electricity bill online")
    assert result.category == Category.UTILITIES
    assert result.source == CategorizationSource.FALLBACK


def test_unmatched_defaults_to_other() -> None:
    result = categorize("Totally Unknown Merchant", "miscellaneous payment")
    assert result.category == Category.OTHER
    assert result.source == CategorizationSource.FALLBACK


def test_case_insensitive_matching() -> None:
    result = categorize("SWIGGY", "SWIGGY ORDER")
    assert result.category == Category.DINING
