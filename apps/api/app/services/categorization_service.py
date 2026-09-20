"""Hybrid transaction categorization: merchant-keyword rules -> description keyword
fallback -> Other. User overrides are tracked separately and never overwritten by
re-categorization (see CategorizationSource)."""

from app.models.enums import CategorizationSource, Category

# Ordered merchant-keyword rules. First match wins. Keys are lowercase substrings
# matched against merchant name; falls back to matching against description.
MERCHANT_RULES: list[tuple[str, Category]] = [
    ("swiggy", Category.DINING),
    ("zomato", Category.DINING),
    ("dominos", Category.DINING),
    ("starbucks", Category.DINING),
    ("mcdonald", Category.DINING),
    ("uber", Category.TRANSPORT),
    ("ola", Category.TRANSPORT),
    ("rapido", Category.TRANSPORT),
    ("metro", Category.TRANSPORT),
    ("irctc", Category.TRANSPORT),
    ("indian oil", Category.TRANSPORT),
    ("petrol", Category.TRANSPORT),
    ("amazon", Category.SHOPPING),
    ("flipkart", Category.SHOPPING),
    ("myntra", Category.SHOPPING),
    ("ajio", Category.SHOPPING),
    ("meesho", Category.SHOPPING),
    ("netflix", Category.ENTERTAINMENT),
    ("spotify", Category.ENTERTAINMENT),
    ("hotstar", Category.ENTERTAINMENT),
    ("prime video", Category.ENTERTAINMENT),
    ("bookmyshow", Category.ENTERTAINMENT),
    ("pvr", Category.ENTERTAINMENT),
    ("rent", Category.HOUSING),
    ("landlord", Category.HOUSING),
    ("society maintenance", Category.HOUSING),
    ("electricity", Category.UTILITIES),
    ("airtel", Category.UTILITIES),
    ("jio", Category.UTILITIES),
    ("vodafone", Category.UTILITIES),
    ("vi ", Category.UTILITIES),
    ("water bill", Category.UTILITIES),
    ("gas cylinder", Category.UTILITIES),
    ("bigbasket", Category.GROCERIES),
    ("blinkit", Category.GROCERIES),
    ("zepto", Category.GROCERIES),
    ("dmart", Category.GROCERIES),
    ("grofers", Category.GROCERIES),
    ("apollo pharmacy", Category.HEALTHCARE),
    ("pharmeasy", Category.HEALTHCARE),
    ("practo", Category.HEALTHCARE),
    ("hospital", Category.HEALTHCARE),
    ("clinic", Category.HEALTHCARE),
    ("byjus", Category.EDUCATION),
    ("udemy", Category.EDUCATION),
    ("coursera", Category.EDUCATION),
    ("tuition", Category.EDUCATION),
    ("school fee", Category.EDUCATION),
    ("makemytrip", Category.TRAVEL),
    ("goibibo", Category.TRAVEL),
    ("indigo", Category.TRAVEL),
    ("air india", Category.TRAVEL),
    ("oyo", Category.TRAVEL),
    ("lic ", Category.INSURANCE),
    ("policybazaar", Category.INSURANCE),
    ("insurance", Category.INSURANCE),
    ("salary", Category.SALARY),
    ("payroll", Category.SALARY),
    ("zerodha", Category.INVESTMENTS),
    ("groww", Category.INVESTMENTS),
    ("mutual fund", Category.INVESTMENTS),
    ("sip ", Category.INVESTMENTS),
    ("upi transfer", Category.TRANSFERS),
    ("neft", Category.TRANSFERS),
    ("imps", Category.TRANSFERS),
]

# Fallback keyword scan over free-text description when no merchant rule matched.
DESCRIPTION_KEYWORDS: list[tuple[str, Category]] = list(MERCHANT_RULES)


class CategorizationResult:
    def __init__(self, category: Category, source: CategorizationSource) -> None:
        self.category = category
        self.source = source


def categorize(merchant_name: str, description: str) -> CategorizationResult:
    merchant_lower = merchant_name.lower()
    description_lower = description.lower()

    for keyword, category in MERCHANT_RULES:
        if keyword in merchant_lower:
            return CategorizationResult(category, CategorizationSource.RULE)

    for keyword, category in DESCRIPTION_KEYWORDS:
        if keyword in description_lower:
            return CategorizationResult(category, CategorizationSource.FALLBACK)

    return CategorizationResult(Category.OTHER, CategorizationSource.FALLBACK)
