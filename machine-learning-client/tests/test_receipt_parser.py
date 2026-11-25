"""Examples of US receipt text after OCR."""

import unittest

from receipts.parser import parse_receipt


class ReceiptParserTests(unittest.TestCase):
    """Check the fields we show a user for review."""

    def test_cash_and_change_are_not_the_sale_total(self):
        """A cash sale can print both a larger tender and a zero balance."""
        text = (
            "Corner Deli\n11/25/2026 12:30\nSubtotal $17.22\n"
            "Sales Tax (8.875%) $1.53\nTOTAL $18.75\nCASH $20.00\n"
            "CHANGE $1.25\nBalance Due $0.00"
        )
        self.assertEqual(
            parse_receipt(text),
            {"date": "2026-11-25", "total_cents": 1875, "tax_cents": 153},
        )

    def test_missing_tax_is_different_from_zero_tax(self):
        """The review screen needs to distinguish unknown tax from an exemption."""
        self.assertIsNone(parse_receipt("Total $23.00")["tax_cents"])
        self.assertEqual(parse_receipt("TAX 0.00")["tax_cents"], 0)

    def test_rate_is_not_a_tax_amount(self):
        """A printed percentage can precede the dollar figure on the same line."""
        self.assertIsNone(parse_receipt("Tax 8.875%")["tax_cents"])
        self.assertEqual(parse_receipt("VAT (15%): $15.00")["tax_cents"], 1500)

    def test_fallback_total_and_thousands_separator(self):
        """An amount-due label alone can identify a purchase price."""
        fields = parse_receipt("2026-11-25\nAmount due: $1,250.40")
        self.assertEqual(fields["total_cents"], 125040)
        self.assertEqual(fields["date"], "2026-11-25")

    def test_repeated_and_conflicting_totals(self):
        """Identical totals agree, while differing printed totals need review."""
        self.assertEqual(parse_receipt("TOTAL 8.10\nTOTAL 8.10")["total_cents"], 810)
        self.assertIsNone(parse_receipt("TOTAL 8.10\nTOTAL 9.10")["total_cents"])

    def test_unlabeled_prices_do_not_fill_in_a_total(self):
        """Partial OCR text can contain prices and an impossible calendar date."""
        fields = parse_receipt("11/31/2026\nCoffee $4.00\nSUBTOTAL $4.00")
        self.assertEqual(fields, {"date": None, "total_cents": None, "tax_cents": None})
