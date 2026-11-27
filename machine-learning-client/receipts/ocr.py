"""Read a receipt image with Tesseract and parse the recognized text."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from receipts.parser import parse_receipt


class ReceiptOCRError(Exception):
    """The OCR engine could not produce receipt text."""


def extract_text(image_path: str | Path) -> str:
    """Recognize an English receipt in a PNG or JPEG file."""
    # The child reads the same file descriptor, so its offset must match seek(0).
    with Path(image_path).open("rb", buffering=0) as image:
        header = image.read(8)
        if not header.startswith((b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")):
            raise ReceiptOCRError("Use a PNG or JPEG receipt image.")
        image.seek(0)
        try:
            result = subprocess.run(
                ["tesseract", "stdin", "stdout", "-l", "eng", "--psm", "6"],
                stdin=image,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=True,
                timeout=30,
            )
        except FileNotFoundError as exc:
            raise ReceiptOCRError("Install Tesseract and add it to PATH.") from exc
        except subprocess.TimeoutExpired as exc:
            raise ReceiptOCRError("OCR timed out after 30 seconds.") from exc
        except subprocess.CalledProcessError as exc:
            raise ReceiptOCRError(
                "Tesseract could not read the image. Check the file and English model."
            ) from exc

    text = result.stdout.strip()
    if not text:
        raise ReceiptOCRError("No text recognized. Try a clearer receipt image.")
    return text


def scan_receipt(image_path: str | Path) -> dict[str, str | int | None]:
    """Return recognized text alongside the existing parser's review fields."""
    text = extract_text(image_path)
    return {"raw_text": text, **parse_receipt(text)}


def main() -> int:
    """Scan one receipt from the command line and print JSON."""
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("image", type=Path, help="path to a PNG or JPEG receipt")
    args = cli.parse_args()
    try:
        result = scan_receipt(args.image)
    except (OSError, ReceiptOCRError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
