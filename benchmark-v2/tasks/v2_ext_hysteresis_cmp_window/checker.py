#!/usr/bin/env python3
import argparse
import csv
import sys


def avg_window(rows, t0, t1, key):
    vals = [float(r[key]) for r in rows if t0 <= float(r["time"]) <= t1]
    if not vals:
        return None
    return sum(vals) / len(vals)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    args = ap.parse_args()
    rows = list(csv.DictReader(open(args.csv, "r", encoding="utf-8")))
    if not rows:
        print("CHECK_FAIL\nempty_csv")
        sys.exit(1)

    low1 = avg_window(rows, 5e-9, 20e-9, "vout")
    high = avg_window(rows, 45e-9, 70e-9, "vout")
    low2 = avg_window(rows, 105e-9, 118e-9, "vout")
    if low1 is None or high is None or low2 is None:
        print("CHECK_FAIL\ninsufficient_samples")
        sys.exit(1)
    ok = (low1 < 0.2) and (high > 0.9) and (low2 < 0.2)
    if not ok:
        print("CHECK_FAIL")
        print(f"low1={low1:.3f} high={high:.3f} low2={low2:.3f}")
        sys.exit(1)
    print("CHECK_PASS")
    print(f"low1={low1:.3f} high={high:.3f} low2={low2:.3f}")


if __name__ == "__main__":
    main()
