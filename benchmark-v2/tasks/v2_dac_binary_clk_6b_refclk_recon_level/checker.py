#!/usr/bin/env python3
import argparse
import csv
import math
import sys


def pick_col(fieldnames, candidates):
    lower = {name.lower(): name for name in fieldnames}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None


def read_wave(csv_path):
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header")
        t_col = pick_col(reader.fieldnames, ["time", "t"])
        y_col = pick_col(reader.fieldnames, ["recon_level", "v(recon_level)"])
        if t_col is None or y_col is None:
            raise ValueError(f"Cannot find required columns in {reader.fieldnames}")
        rows = [(float(r[t_col]), float(r[y_col])) for r in reader]
    if not rows:
        raise ValueError("CSV has no rows")
    return rows


def nearest_value(rows, t_query):
    best_t, best_v = rows[0]
    best_dt = abs(best_t - t_query)
    for t, v in rows[1:]:
        dt = abs(t - t_query)
        if dt < best_dt:
            best_t, best_v, best_dt = t, v, dt
    return best_v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--tol", type=float, default=0.035)
    args = ap.parse_args()

    rows = read_wave(args.csv)
    lsb = 1.2 / 63.0
    checks = [
        (35e-9, 1),
        (55e-9, 2),
        (75e-9, 3),
        (95e-9, 5),
        (115e-9, 37),
    ]
    fails = []
    for t_s, code in checks:
        got = nearest_value(rows, t_s)
        exp = code * lsb
        if math.fabs(got - exp) > args.tol:
            fails.append((t_s, exp, got))

    if fails:
        print("CHECK_FAIL")
        for t_s, exp, got in fails:
            print(f"t={t_s:.3e}s expected={exp:.6f} got={got:.6f}")
        sys.exit(1)
    print("CHECK_PASS")


if __name__ == "__main__":
    main()
