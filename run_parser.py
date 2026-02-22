"""
Run the equation parser: read equations from a .txt file (one per line),
generate a separate JSON structure for each line (same schema rules), write .json.

Usage:
    python run_parser.py                    # uses sample_equations.txt
    python run_parser.py input.txt          # output: input.json
    python run_parser.py input.txt out.json
"""

import sys
from pathlib import Path

from equation_parser import parse_equations_file


def main():
    if len(sys.argv) >= 2:
        input_file = Path(sys.argv[1])
        output_file = Path(sys.argv[2]) if len(sys.argv) >= 3 else input_file.with_suffix(".json")
    else:
        input_file = Path(__file__).parent / "sample_equations.txt"
        output_file = Path(__file__).parent / "sample_equations.json"

    if not input_file.exists():
        print(f"Error: input file not found: {input_file}")
        sys.exit(1)

    result = parse_equations_file(input_file, output_path=output_file)
    print(f"Parsed {result['count']} equations from {result['source_file']}")
    print(f"Output: {output_file} (one JSON structure per line, same rules)")


if __name__ == "__main__":
    main()
