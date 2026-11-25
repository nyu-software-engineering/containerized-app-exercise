The receipt parser takes OCR text from a US receipt and returns a draft for review.
parse_receipt(text) returns date (YYYY-MM-DD), total_cents, and tax_cents.
Missing fields and conflicting amounts are returned as None. An explicit zero is kept.

Run the parser tests from this directory with Python 3.10 or later:
    python -m unittest discover -s tests
