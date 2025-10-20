import glob
import os
import pandas as pd

# 1. Folder containing your CSVs
folder_path = "./"

# 2. Grab every .csv file
all_files = glob.glob(os.path.join(folder_path, "*.csv"))

# 3. Read & concatenate
df_list = [pd.read_csv(f) for f in all_files]
combined = pd.concat(df_list, ignore_index=True)

# 4. Add HomeTeamFull and AwayTeamFull columns
combined['HomeTeamFull'] = combined['HomeTeam']
combined['AwayTeamFull'] = combined['AwayTeam']

# 5. If TaggedPitchType is NOT empty/null/undefined → use it for AutoPitchType
combined['AutoPitchType'] = combined.apply(
    lambda row: row['TaggedPitchType']
    if pd.notna(row['TaggedPitchType']) 
    and str(row['TaggedPitchType']).strip().lower() not in ['', 'none', 'null', 'undefined']
    else row['AutoPitchType'],
    axis=1
)

# 6. Save the combined CSV
combined.to_csv("combined.csv", index=False)

print(f"✅ Merged {len(all_files)} files → combined.csv ({combined.shape[0]} rows)")
print("✅ HomeTeamFull / AwayTeamFull added and AutoPitchType updated from TaggedPitchType where available.")
