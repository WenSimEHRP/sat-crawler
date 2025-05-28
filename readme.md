# SAT Questions Crawler

Simple yet _worksful_ question crawler.
Fetched data is available in json and cbor formats.
Use at your own risk.

## Usage

- Fetching questions: `crawl.py`
- Randomly select questions & make html/pdf output: `make_pdf.py`
  - Specify paper size using `--paper-size`. This by default uses us-letter.
  - Specify output file name using `--output`.
  - Answers:
    - `--answers-only`: only generate the answers html/pdf.
    - `--no-answers`: don't generate any answers.

- Examples:
  - `./make_pdf.py --paper-size letter --output questions --no-answers`
    - Set paper size to letter.
    - Set output prefix to "questions".
    - Don't generate answers.
  - `./make_pdf.py --paper-size a4 --output abcde --answers-only`
    - Set paper size to A4.
    - Set output prefix to "abcde".
    - Only generate answers.
  - `./make_pdf.py`
    - Default paper size (letter).
    - Default output prefix (questions).
    - Generate answers _and_ questions.

## Installing Dependencies

### UNIX/Linux/MacOS/Windows

For pdf and html appearance consistency, please install the font [`noto-serif`](https://fonts.google.com/noto/specimen/Noto+Serif).

Install dependencies via `pip3 install -r requirements.txt`.

### Using Nix/NixOS

Use `nix-shell` to enter the development environment.
