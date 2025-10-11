import pandas as pd

# Read the CSV file
df = pd.read_csv('combined.csv')

# Create new columns using existing ones
df['HomeTeamFull'] = df['HomeTeam']
df['AwayTeamFull'] = df['AwayTeam']

# Save the updated CSV (overwrite or new file)
df.to_csv('combined.csv', index=False)

print("✅ HomeTeamFull and AwayTeamFull columns created successfully.")
