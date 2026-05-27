#!/usr/bin/env python3
import argparse
import csv
import math
import sys


def read_rows(path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return [(float(x["time"]), float(x["out_level"])) for x in r]


def near(rows, t):
    return min(rows, key=lambda x: abs(x[0] - t))[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--tol", type=float, default=0.04)
    args = ap.parse_args()
    rows = read_rows(args.csv)
    lsb = 1.2 / 7.0
    checks = [(35e-9, 1), (55e-9, 2), (75e-9, 2), (95e-9, 4)]
    bad = []
    for t, code in checks:
        exp = code * lsb
        got = near(rows, t)
        if math.fabs(got - exp) > args.tol:
            bad.append((t, exp, got))
    if bad:
        print("CHECK_FAIL")
        for t, exp, got in bad:
            print(f"t={t:.3e}s expected={exp:.6f} got={got:.6f}")
        sys.exit(1)
    print("CHECK_PASS")


if __name__ == "__main__":
    main()
