import pandas as pd
import re
# Replace with your CSV file path
INPUT_CSV = "/Users/choijinhyeok/Documents/20251010/Complete_CSV/treat.csv"
outfile = "/Users/choijinhyeok/Documents/20251010/Complete_CSV/treat2.csv"
df = pd.read_csv(INPUT_CSV,dtype=str)


pattern = re.compile(
    r"^(?:(?P<journal>.+)\.)?\s*(?:(?P<year>(16|17|18|19|20)\d{2})(?:\s[A-Za-z]{3}(?:\s\d{1,2})?)?"
    r"(?:\s\d{1,2})?(?:-\d{1,2})?(?:\s[A-Za-z]{3}(?:-\s?[A-Za-z]{3})?)?"
    r"(?:\s(Spring|spring|Summer|summer|Fall|fall|Autumn|autumn|Winter|winter))?"
    r"(?:[-\s]?(Spring|spring|Summer|summer|Fall|fall|Autumn|autumn|Winter|winter))?"
    r"(?:\s(January|February|March|April|May|June|July|August|September|October|November|December))?"
    r"(?:[-\s]?(January|February|March|April|May|June|July|August|September|October|November|December))?)?;"
)

def extract_group(x, group):
    m = pattern.match(str(x).strip())
    return m.group(group).strip() if m and m.group(group) else None

df["journal"] = df["Article Citation"].apply(lambda x: extract_group(x, "journal"))
df["year"] = df["Article Citation"].apply(lambda x: extract_group(x, "year"))

matches = df["Article Citation"].astype(str).apply(lambda x: bool(pattern.match(x.strip())))
invalid = df[~matches]  # only rows where pattern failed

invalid.to_csv("/Users/choijinhyeok/Documents/20251010/Complete_CSV/invalid_rows.csv", index=False)
print(f"Saved {len(invalid)} invalid rows → invalid_rows.csv")


print(f"✅ Pattern matched all rows" if invalid.empty else f"❌ {len(invalid)} rows failed pattern:\n", invalid["Article Citation"].head(10).tolist())
