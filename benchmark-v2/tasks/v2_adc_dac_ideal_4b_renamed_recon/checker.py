#!/usr/bin/env python3
import argparse
import csv
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    args = ap.parse_args()
    with open(args.csv, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("CHECK_FAIL")
        print("empty_csv")
        sys.exit(1)
    codes = set()
    vout = []
    vin = []
    for r in rows:
        c = 0
        if float(r["q0"]) > 0.45:
            c += 1
        if float(r["q1"]) > 0.45:
            c += 2
        if float(r["q2"]) > 0.45:
            c += 4
        if float(r["q3"]) > 0.45:
            c += 8
        codes.add(c)
        vout.append(float(r["recon_level"]))
        vin.append(float(r["analog_in"]))
    unique_codes = len(codes)
    vout_span = max(vout) - min(vout)
    vin_span = max(vin) - min(vin)
    ok = unique_codes >= 12 and vout_span > 0.6 and vin_span > 0.6
    if not ok:
        print("CHECK_FAIL")
        print(f"unique_codes={unique_codes} vout_span={vout_span:.3f} vin_span={vin_span:.3f}")
        sys.exit(1)
    print("CHECK_PASS")
    print(f"unique_codes={unique_codes} vout_span={vout_span:.3f} vin_span={vin_span:.3f}")


if __name__ == "__main__":
    main()
