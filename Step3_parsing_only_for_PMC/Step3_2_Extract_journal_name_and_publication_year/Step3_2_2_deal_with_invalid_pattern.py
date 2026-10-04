##################################
You should manually extract journal name and years from "invalid_rows.csv", and create "invalid_rows_fixed.csv"
##################################

OUTPUT_CSV="step3normalized_with_journal_year.csv"
# Concatenate "invalid_rows.csv"

# Read manually edited file (must include 'journal' and 'year')
edited = pd.read_csv("/Users/choijinhyeok/Documents/20251010/Complete_CSV/invalid_rows_fixed.csv", dtype=str)

# Merge back on unique identifier (e.g. AccessionID)
df.update(edited.set_index("AccessionID"))

# Save the fully normalized dataset
df.to_csv(OUTPUT_CSV, index=False)
print("✅ Merged fixed rows and saved → normalized_with_journal_year.csv")
