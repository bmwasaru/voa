#!/usr/bin/env python3
"""
Clean VOA Swahili sentence CSV files.

Default behaviour:
- Reads one CSV file or every .csv file inside a folder.
- Writes cleaned files to a separate output folder.
- Keeps one sentence per row, with no header by default.
- Removes VOA page/UI/audio-player/comment noise.
- Removes duplicate sentences within each file.

Examples:
    python scripts/clean_voa_csv.py sentences --output-dir sentences_cleaned
    python scripts/clean_voa_csv.py sentences/01-03-24.csv --output-dir cleaned
    python scripts/clean_voa_csv.py sentences --overwrite --backup
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple


# Exact rows to leave out. These are normalized to lowercase before checking.
# Keep social media terms as exact matches only so real article sentences mentioning
# Facebook/Twitter/WhatsApp are not accidentally removed.
NOISE_EXACT = {
    "",
    "live",
    "forum",
    "jiunge",
    "shirikisha",
    "copy link",
    "facebook",
    "twitter",
    "whatsapp",
    "email",
    "print",
    "ona maoni",
    "follow us",
    "zinazohusiana",
    "no media source currently available",
    "the code has been copied to your clipboard.",
    "the code has been copied to your clipboard",
    "the url has been copied to your clipboard.",
    "the url has been copied to your clipboard",
    "please enable javascript to view the",
    "comments powered by disqus.",
    "comments powered by disqus",
    "voa swahili audio tube",
    "voa audio tube",
    "audio tube",
    "duniani leo video tube",
    "video tube",
    "alfajiri",
    "jioni",
    "duniani leo",
    "voa express",
    "kwa undani",
    "dkt.",
    "mp3",
}

# Rows matching any of these patterns will be removed.
NOISE_PATTERNS = [
    re.compile(r"\bVOA\s+Swahili\s+Audio\s+Tube\b", re.IGNORECASE),
    re.compile(r"\bDuniani\s+Leo\s+Video\s+Tube\b", re.IGNORECASE),
    re.compile(r"\bAudio\s+Tube\b", re.IGNORECASE),
    re.compile(r"\bVideo\s+Tube\b", re.IGNORECASE),
    re.compile(r"copied\s+to\s+your\s+clipboard", re.IGNORECASE),
    re.compile(r"comments\s+powered\s+by\s+Disqus", re.IGNORECASE),
    re.compile(r"please\s+enable\s+javascript\s+to\s+view", re.IGNORECASE),
    re.compile(r"no\s+media\s+source\s+currently\s+available", re.IGNORECASE),
    re.compile(r"^\s*\d+\s*kbps\s*(\|\s*)?mp3\s*$", re.IGNORECASE),
    re.compile(r"^\s*\d+\s*kbps\s*$", re.IGNORECASE),
]

# Drop obvious URL rows. These sometimes enter the CSV when related links are scraped.
URL_PATTERN = re.compile(r"^(https?://|www\.)", re.IGNORECASE)

# Remove invisible characters that commonly appear after web scraping.
INVISIBLE_CHARS = {
    "\ufeff": "",
    "\u200b": "",
    "\u200c": "",
    "\u200d": "",
    "\xa0": " ",
}


def normalize_sentence(text: str) -> str:
    """Normalize whitespace and remove wrapping quotes/newlines from one scraped row."""
    if text is None:
        return ""

    for old, new in INVISIBLE_CHARS.items():
        text = text.replace(old, new)

    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    text = re.sub(r"\s+", " ", text).strip()

    # Remove only wrapping quotes/spaces left by the old CSV writer.
    text = text.strip(" \"“”")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalized_key(text: str) -> str:
    """Create a lowercase comparison key for duplicate and noise checks."""
    text = normalize_sentence(text).casefold()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_noise(sentence: str, min_chars: int = 2) -> bool:
    """Return True when a row is UI/audio/comment noise rather than article text."""
    cleaned = normalize_sentence(sentence)
    key = normalized_key(cleaned)

    if not key:
        return True

    if len(cleaned) < min_chars:
        return True

    if key in NOISE_EXACT:
        return True

    if URL_PATTERN.match(cleaned):
        return True

    return any(pattern.search(cleaned) for pattern in NOISE_PATTERNS)


def read_sentence_rows(csv_path: Path) -> Iterable[str]:
    """Read a CSV and yield text rows. Handles one-column sentence CSVs and messy rows."""
    with csv_path.open("r", newline="", encoding="utf-8", errors="replace") as infile:
        reader = csv.reader(infile)
        for row in reader:
            if not row:
                continue

            # Existing VOA sentence CSVs are one-column files. If a row has multiple
            # cells because of older formatting, join non-empty cells safely.
            raw_text = " ".join(cell for cell in row if cell is not None)
            yield raw_text


def clean_sentences(
    rows: Iterable[str],
    *,
    keep_duplicates: bool = False,
    min_chars: int = 2,
) -> Tuple[List[str], dict]:
    """Clean rows and return (sentences, stats)."""
    cleaned_rows: List[str] = []
    seen = set()
    stats = {
        "input_rows": 0,
        "kept_rows": 0,
        "blank_or_noise_rows": 0,
        "duplicate_rows": 0,
    }

    for raw in rows:
        stats["input_rows"] += 1
        sentence = normalize_sentence(raw)

        if is_noise(sentence, min_chars=min_chars):
            stats["blank_or_noise_rows"] += 1
            continue

        key = normalized_key(sentence)
        if not keep_duplicates and key in seen:
            stats["duplicate_rows"] += 1
            continue

        seen.add(key)
        cleaned_rows.append(sentence)

    stats["kept_rows"] = len(cleaned_rows)
    return cleaned_rows, stats


def write_clean_csv(sentences: Sequence[str], output_path: Path, *, header: bool = False) -> None:
    """Write cleaned sentences to CSV, one sentence per row."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        if header:
            writer.writerow(["sentence"])
        for sentence in sentences:
            writer.writerow([sentence])


def discover_csv_files(input_path: Path) -> List[Path]:
    """Return one CSV file or all CSV files in a directory."""
    if input_path.is_file():
        if input_path.suffix.lower() != ".csv":
            raise ValueError(f"Input file is not a CSV: {input_path}")
        return [input_path]

    if input_path.is_dir():
        return sorted(input_path.glob("*.csv"))

    raise FileNotFoundError(f"Input path not found: {input_path}")


def clean_csv_file(
    csv_path: Path,
    *,
    output_dir: Path | None,
    overwrite: bool,
    backup: bool,
    keep_duplicates: bool,
    header: bool,
    min_chars: int,
) -> dict:
    """Clean one CSV file and write the result."""
    sentences, stats = clean_sentences(
        read_sentence_rows(csv_path),
        keep_duplicates=keep_duplicates,
        min_chars=min_chars,
    )

    if overwrite:
        output_path = csv_path
        if backup:
            backup_path = csv_path.with_suffix(csv_path.suffix + ".bak")
            shutil.copy2(csv_path, backup_path)
    else:
        if output_dir is None:
            output_dir = csv_path.parent / "cleaned"
        output_path = output_dir / csv_path.name

    write_clean_csv(sentences, output_path, header=header)
    stats["input_file"] = str(csv_path)
    stats["output_file"] = str(output_path)
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean VOA Swahili scraped sentence CSV files."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="CSV file or folder containing daily CSV files, e.g. sentences or sentences/01-03-24.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Folder for cleaned CSV files. Default: <input_folder>/cleaned when not overwriting.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the original CSV file(s). Use with --backup if you want safety copies.",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="When using --overwrite, first create .csv.bak copies of the original files.",
    )
    parser.add_argument(
        "--keep-duplicates",
        action="store_true",
        help="Keep duplicate sentences. By default duplicates within each file are removed.",
    )
    parser.add_argument(
        "--header",
        action="store_true",
        help="Write a 'sentence' header row. Default is no header to match your existing daily CSV files.",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=2,
        help="Remove rows shorter than this after cleaning. Default: 2.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    csv_files = discover_csv_files(args.input)

    if not csv_files:
        print(f"No CSV files found in {args.input}")
        return

    totals = {
        "files": 0,
        "input_rows": 0,
        "kept_rows": 0,
        "blank_or_noise_rows": 0,
        "duplicate_rows": 0,
    }

    for csv_file in csv_files:
        stats = clean_csv_file(
            csv_file,
            output_dir=args.output_dir,
            overwrite=args.overwrite,
            backup=args.backup,
            keep_duplicates=args.keep_duplicates,
            header=args.header,
            min_chars=args.min_chars,
        )

        totals["files"] += 1
        for key in ["input_rows", "kept_rows", "blank_or_noise_rows", "duplicate_rows"]:
            totals[key] += stats[key]

        print(
            f"Cleaned {stats['input_file']} -> {stats['output_file']} | "
            f"input={stats['input_rows']}, kept={stats['kept_rows']}, "
            f"noise={stats['blank_or_noise_rows']}, duplicates={stats['duplicate_rows']}"
        )

    print(
        "Done | "
        f"files={totals['files']}, input={totals['input_rows']}, kept={totals['kept_rows']}, "
        f"noise={totals['blank_or_noise_rows']}, duplicates={totals['duplicate_rows']}"
    )


if __name__ == "__main__":
    main()
