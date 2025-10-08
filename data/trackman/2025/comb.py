from pathlib import Path
import pandas as pd

# ================== CONFIG ==================
BASE_DIR = Path(__file__).resolve().parent   # folder that contains 02, 03, 04, ...
OUTPUT_CSV = BASE_DIR / "combined.csv"
SIZE_THRESHOLD_BYTES = 190 * 1024            # 190 KB
EXCLUDE_TOKEN = "-bp-"                       # case-insensitive match
VERBOSE = True
# ============================================

def is_two_digit_number(name: str) -> bool:
    return len(name) == 2 and name.isdigit()

def find_eligible_csvs(base_dir: Path):
    eligible = []
    # months
    month_dirs = [p for p in base_dir.iterdir()
                  if p.is_dir() and is_two_digit_number(p.name)]
    for month_dir in sorted(month_dirs):
        try:
            day_dirs = [p for p in month_dir.iterdir()
                        if p.is_dir() and is_two_digit_number(p.name)]
        except PermissionError:
            if VERBOSE:
                print(f"SKIP (perm): {month_dir}")
            continue

        for day_dir in sorted(day_dirs):
            csv_dir = day_dir / "csv"
            if not csv_dir.is_dir():
                if VERBOSE:
                    print(f"SKIP (no csv/): {csv_dir}")
                continue

            for f in sorted(csv_dir.glob("*.csv")):
                name_lc = f.name.lower()
                try:
                    size_ok = f.stat().st_size > SIZE_THRESHOLD_BYTES
                except (OSError, PermissionError):
                    if VERBOSE:
                        print(f"SKIP (stat fail): {f}")
                    continue

                if EXCLUDE_TOKEN in name_lc:
                    if VERBOSE:
                        print(f"SKIP (-BP-): {f.name}")
                    continue
                if not size_ok:
                    if VERBOSE:
                        print(f"SKIP (small ≤190KB): {f.name}")
                    continue

                eligible.append(f)
                if VERBOSE:
                    print(f"OK: {f} ({f.stat().st_size} bytes)")
    return eligible

def build_union_columns(files):
    """Read headers to build a stable union of columns.
       Ensure HomeNameFull and AwayNameFull are included."""
    master_cols = []
    seen = set()
    saw_home = False
    saw_away = False

    for f in files:
        try:
            cols = list(pd.read_csv(f, nrows=0).columns)
        except Exception as e:
            if VERBOSE:
                print(f"SKIP (header read error): {f} ({e})")
            continue

        for c in cols:
            if c not in seen:
                seen.add(c)
                master_cols.append(c)
        saw_home = saw_home or ("HomeTeam" in cols)
        saw_away = saw_away or ("AwayTeam" in cols)

    # Always include requested new columns at the end (stable position)
    for extra in ["HomeNameFull", "AwayNameFull"]:
        if extra not in seen:
            master_cols.append(extra)
            seen.add(extra)

    return master_cols

def write_combined_csv(files, master_cols, output_csv: Path):
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    first = True
    total_rows = 0
    kept_files = 0

    for f in files:
        try:
            df = pd.read_csv(f, engine="python", on_bad_lines="skip")
        except Exception as e:
            if VERBOSE:
                print(f"SKIP (read error): {f} ({e})")
            continue

        if df.empty:
            if VERBOSE:
                print(f"SKIP (empty): {f}")
            continue

        # ==== Add required columns per row ====
        # HomeNameFull = HomeTeam; AwayNameFull = AwayTeam
        if "HomeTeam" in df.columns:
            df["HomeNameFull"] = df["HomeTeam"]
        else:
            df["HomeNameFull"] = pd.NA

        if "AwayTeam" in df.columns:
            df["AwayNameFull"] = df["AwayTeam"]
        else:
            df["AwayNameFull"] = pd.NA
        # ======================================

        # Align to union columns (includes HomeNameFull/AwayNameFull)
        df = df.reindex(columns=master_cols)

        df.to_csv(output_csv, mode="w" if first else "a",
                  index=False, header=first)
        first = False
        total_rows += len(df)
        kept_files += 1
        if VERBOSE:
            print(f"APPENDED: {f} (+{len(df)} rows)")

    return kept_files, total_rows

def main():
    print(f"Base directory: {BASE_DIR}")
    eligible = find_eligible_csvs(BASE_DIR)

    if not eligible:
        print("No eligible CSVs found (size > 190KB and not containing '-BP-').")
        return

    master_cols = build_union_columns(eligible)
    if not master_cols:
        print("Could not determine any columns from eligible files.")
        return

    kept_files, total_rows = write_combined_csv(eligible, master_cols, OUTPUT_CSV)
    if kept_files == 0:
        print("No rows written. All files failed to read or were empty after filtering.")
    else:
        print(f"Done. Wrote {total_rows} rows from {kept_files} files to:\n{OUTPUT_CSV}")

if __name__ == "__main__":
    main()
