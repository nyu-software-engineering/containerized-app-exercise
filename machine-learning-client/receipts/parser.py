"""Extract printed dates and amounts from OCR text on US receipts."""

from datetime import datetime
import re


_MONEY = r"(-?\d{1,3}(?:,\d{3})+\.\d{2}|-?\d+\.\d{2})"
_TOTAL = re.compile(
    rf"(grand total|total due|total|amount due|balance due)\s*:?\s*\$?\s*{_MONEY}",
    re.IGNORECASE,
)
_TAX = re.compile(
    r"(?:total tax|sales tax|tax|VAT)\s*(?:\(?\d+(?:\.\d+)?\s*%\)?)?"
    rf"\s*:?\s*\$?\s*{_MONEY}",
    re.IGNORECASE,
)
_DATE = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b")


def _cents(amount: str) -> int:
    return int(amount.replace(",", "").replace(".", ""))


def _printed_date(text: str) -> str | None:
    for match in _DATE.finditer(text):
        value = match.group()
        fmt = "%m/%d/%Y" if "/" in value else "%Y-%m-%d"
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _unambiguous(values: set[int]) -> int | None:
    return next(iter(values)) if len(values) == 1 else None


def parse_receipt(text: str) -> dict[str, str | int | None]:
    """Return a date and integer cents. Missing or conflicting amounts stay blank."""
    totals = set()
    balances = set()
    taxes = set()
    for line in text.splitlines():
        line = " ".join(line.split())
        total = _TOTAL.fullmatch(line)
        if total:
            label, amount = total.groups()
            if label.lower() in {"amount due", "balance due"}:
                balances.add(_cents(amount))
            else:
                totals.add(_cents(amount))
        tax = _TAX.fullmatch(line)
        if tax:
            taxes.add(_cents(tax.group(1)))

    return {
        "date": _printed_date(text),
        "total_cents": _unambiguous(totals or balances),
        "tax_cents": _unambiguous(taxes),
    }
