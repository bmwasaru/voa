import argparse
from pathlib import Path

import pandas as pd
from kiswahili_speech_norm import normalize_kiswahili_speech


def normalize_directory(input_dir, output_file, profile="asr"):
    input_dir = Path(input_dir)
    rows = []

    for csv_file in sorted(input_dir.glob("*.csv")):
        try:
            df = pd.read_csv(csv_file, header=None)
        except Exception as e:
            print(f"Skipping {csv_file.name}: {e}")
            continue

        for row_idx, row in df.iterrows():
            for col_idx, value in row.items():
                if pd.isna(value):
                    continue

                raw_text = str(value).strip()
                if not raw_text:
                    continue

                normalized_text = normalize_kiswahili_speech(
                    raw_text,
                    profile=profile
                )

                rows.append({
                    "source_file": csv_file.name,
                    "row_index": row_idx,
                    "column_index": col_idx,
                    "raw_text": raw_text,
                    "normalized_text": normalized_text,
                    "profile": profile,
                })

    output_df = pd.DataFrame(rows)
    output_df.to_csv(output_file, index=False, encoding="utf-8")

    print(f"Done. Saved {len(output_df)} rows to {output_file}")

    txt_output = Path(output_file).with_suffix(".txt")

    with open(txt_output, "w", encoding="utf-8") as f:
        for text in output_df["normalized_text"]:
            f.write(text + "\n")

    print(f"Also saved plain text corpus to {txt_output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", help="Directory containing CSV files")
    parser.add_argument("output_file", help="Output combined CSV file")
    parser.add_argument(
        "--profile",
        choices=["asr", "tts"],
        default="asr",
        help="Normalization profile"
    )

    args = parser.parse_args()

    normalize_directory(
        input_dir=args.input_dir,
        output_file=args.output_file,
        profile=args.profile
    )