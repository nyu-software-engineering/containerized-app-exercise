The receipt parser takes OCR text from a US receipt and returns a draft for review.
parse_receipt(text) returns date (YYYY-MM-DD), total_cents, and tax_cents.
Missing fields and conflicting amounts are returned as None. An explicit zero is kept.

Scan one English-language receipt from a PNG or JPEG with Python 3.10+.
Install Tesseract 5 with English language data and put tesseract on PATH.
On macOS use brew install tesseract. On Ubuntu or Debian install the packages
tesseract-ocr and tesseract-ocr-eng. Run these commands from this directory:

    python -m receipts.ocr tests/fixtures/corner-deli.png

The command prints JSON with raw_text, date, total_cents, and tax_cents.
The sample is a synthetic receipt dated 2026-11-25 with a total of 1875 cents
and tax of 153 cents. Replace its path with your own receipt, quoted if needed.

Run all tests, including the sample scan:
    python -m unittest discover -s tests
