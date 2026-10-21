#!/usr/bin/env python3
"""Rebuild the whole gallery: collect raw sources -> extract ids -> build site data.

    python3 update.py

Steps:
  1. collect.py       fetch all galleries   -> turbowarp_extensions.json
  2. fetch_ids.py     download every .js     -> extension_ids.json
  3. build_data.py    merge by extension id  -> extensions.json
"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = ["collect.py", "fetch_ids.py", "build_data.py"]


def main():
    for step in STEPS:
        print(f"\n=== {step} ===")
        rc = subprocess.call([sys.executable, os.path.join(HERE, step)])
        if rc != 0:
            sys.exit(f"{step} упал с кодом {rc}")
    print("\nГотово: extensions.json обновлён.")


if __name__ == "__main__":
    main()
