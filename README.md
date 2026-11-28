[![ML client CI](https://github.com/software-students-fall2026/containerized-app-exercise-Faker_VS_Bin/actions/workflows/ml-client-ci.yml/badge.svg?branch=main)](https://github.com/software-students-fall2026/containerized-app-exercise-Faker_VS_Bin/actions/workflows/ml-client-ci.yml)
[![Lint-free](https://github.com/software-students-fall2026/containerized-app-exercise-Faker_VS_Bin/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/software-students-fall2026/containerized-app-exercise-Faker_VS_Bin/actions/workflows/lint.yml)

# Receipt Scanner & Expense Tracker

Our project will scan receipts, let users review the extracted information, and
track spending. The current implementation is a command-line OCR client: it reads
English-language PNG/JPEG receipts with Tesseract and returns recognized text,
the purchase date, total, and tax for review. Amounts are integer cents; missing
or conflicting fields are `null`.

The Flask dashboard, receipt APIs, MongoDB integration, and three-service Docker
Compose setup are planned work. The commands below run the existing OCR client
independently; no database, environment variables, or API keys are required yet.
See the [assignment requirements](./instructions.md).

## Run OCR with Docker

Install Docker with a running Linux container engine (Docker Desktop on macOS
or Windows, or Docker Engine on Linux). Run these commands from the repository
root. Python and Tesseract are installed inside the image.

```sh
docker build -t receipt-ocr ./machine-learning-client
docker run --rm receipt-ocr samples/corner-deli.png
```

The bundled synthetic receipt produces a result with these fields, plus
`raw_text` containing the recognized receipt text:

```json
{
  "date": "2026-11-25",
  "total_cents": 1875,
  "tax_cents": 153
}
```

To scan your own image, mount a directory containing receipts as read-only.
For example, create a `receipts` directory at the repository root and put
`my-receipt.jpg` in it.

macOS/Linux shell:

```sh
docker run --rm \
  --mount "type=bind,source=$(pwd)/receipts,target=/data,readonly" \
  receipt-ocr /data/my-receipt.jpg
```

Windows PowerShell:

```powershell
docker run --rm --mount "type=bind,source=$((Get-Location).Path)/receipts,target=/data,readonly" receipt-ocr /data/my-receipt.jpg
```

The mounted files must be readable by the container's non-root user. Run
`docker run --rm receipt-ocr --help` for usage. Invalid or unreadable images
produce an error on stderr and a nonzero exit code; successful scans print JSON
to stdout. The client processes one image and exits.

## Test the OCR client

Build the test target and run the existing tests, including recognition of the
real sample image with Tesseract:

```sh
docker build --target test -t receipt-ocr-test ./machine-learning-client
docker run --rm receipt-ocr-test
```

The test command uses pytest and fails if coverage of the `receipts` package is
below 80%. Test dependencies are installed from `Pipfile.lock`; the final runtime
image contains the OCR code and Tesseract without the test tools.

To run the formatting and lint checks in the same test image:

```sh
docker run --rm receipt-ocr-test black --check receipts tests
docker run --rm receipt-ocr-test pylint receipts tests
```

For development without Docker, see the
[client setup instructions](./machine-learning-client/readme.txt).

## Continuous integration

`ML client CI` runs for pull requests targeting `main`/`master`, pushes to those
branches, and manual dispatches. It builds the test image, runs pytest with the
80% coverage threshold, builds the runtime image, and checks both a successful
sample scan and rejection of an invalid image. It does not publish images.

The separate `lint-free` workflow checks Black and Pylint for each subsystem
that contains Python files. The ML badge will report a result after the new
workflow first runs on `main`. A web-app build/test workflow and its badge will
be added when that subsystem is implemented.
