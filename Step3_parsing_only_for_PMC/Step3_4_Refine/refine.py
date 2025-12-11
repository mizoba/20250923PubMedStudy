import pandas as pd

csv_path = "/Users/choijinhyeok/Documents/ResearchJamaPvalue/20251010/Step2Complete_CSV/step3WithEveryFlag.csv"
output_path = "/Users/choijinhyeok/Documents/ResearchJamaPvalue/20251010/Step2Complete_CSV/step4Refined.csv"

df = pd.read_csv(csv_path)

# Drop the unwanted columns
df = df.drop(columns=['journal', 'PMID', 'PublicationType'])

# Rename AccessionID to pmcid
df = df.rename(columns={'AccessionID': 'pmcid'})

# Save to a new CSV (without the index column)
df.to_csv(output_path, index=False)

print("Transformation complete. Saved to:", output_path)