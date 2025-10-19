"""
Sample entrypoint to be replaced with your actual program.
Supports both function-style import (PROGRAM_ENTRYPOINT=runner.py:main)
And subprocess-style call (PROGRAM_ENTRYPOINT=python runner.py).

Expected behavior:
- Read input Excel files from input_paths
- Write any outputs into output_dir
- Return 0 on success, non-zero on failure
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import List


def main(input_paths: List[str], output_dir: str, **options):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    # Example: copy inputs into outputs and write a small report
    report = out / "report.txt"
    with report.open("w", encoding="utf-8") as f:
        f.write("Runner example executed\n")
        f.write(f"Options: {json.dumps(options)}\n")
        f.write("Inputs:\n")
        for p in input_paths:
            f.write(f" - {Path(p).name}\n")
    # Produce a dummy Excel-like output to test listing
    (out / "result_example.csv").write_text("col1,col2\n1,2\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    # Subprocess mode: python runner.py --inputs "[paths]" --out DIR --options "{...}"
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--options", default="{}")
    args = ap.parse_args()
    inputs = json.loads(args.inputs)
    opts = json.loads(args.options)
    code = main(input_paths=inputs, output_dir=args.out, **opts)
    sys.exit(int(code or 0))
