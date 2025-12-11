
import pandas as pd
import glob
import os

# path to the folder containing all the batch CSVs
FOLDER = "/Volumes/ssd/oa_bulk_data/oa_bulk/oa_comm/xml"   # 🔁 change this path
OUTPUT = "/Volumes/ssd/work/oa_comm/total_metadata.csv"

# find all csv files in the folder
csv_files = glob.glob(os.path.join(FOLDER, "*.csv"))

print(f"Found {len(csv_files)} CSV files")

# read and concatenate them (skip header from 2nd file onward)
df_list = [pd.read_csv(f) for f in csv_files]
combined = pd.concat(df_list, ignore_index=True)

# save to one merged CSV
combined.to_csv(OUTPUT, index=False)
print(f"✅ Combined CSV saved to {OUTPUT}")


import pandas as pd
import glob
import os

# path to the folder containing all the batch CSVs
FOLDER = "/Volumes/ssd/oa_bulk_data/oa_bulk/oa_noncomm/xml"   # 🔁 change this path
OUTPUT = "/Volumes/ssd/work/oa_noncomm/total_metadata.csv"

# find all csv files in the folder
csv_files = glob.glob(os.path.join(FOLDER, "*.csv"))

print(f"Found {len(csv_files)} CSV files")

# read and concatenate them (skip header from 2nd file onward)
df_list = [pd.read_csv(f) for f in csv_files]
combined = pd.concat(df_list, ignore_index=True)

# save to one merged CSV
combined.to_csv(OUTPUT, index=False)
print(f"✅ Combined CSV saved to {OUTPUT}")
len(combined)


import pandas as pd
import glob
import os

# path to the folder containing all the batch CSVs
FOLDER = "/Volumes/ssd/oa_bulk_data/oa_bulk/oa_other/xml"   # 🔁 change this path
OUTPUT = "/Volumes/ssd/work/oa_other/total_metadata.csv"

# find all csv files in the folder
csv_files = glob.glob(os.path.join(FOLDER, "*.csv"))

print(f"Found {len(csv_files)} CSV files")

# read and concatenate them (skip header from 2nd file onward)
df_list = [pd.read_csv(f) for f in csv_files]
combined = pd.concat(df_list, ignore_index=True)

# save to one merged CSV
combined.to_csv(OUTPUT, index=False)
print(f"✅ Combined CSV saved to {OUTPUT}")

len(combined)

# 중복 행 제거 (완전히 동일한 행)
combined = combined.drop_duplicates()
len(combined)



import pandas as pd
import glob
import os

# path to the folder containing all the batch CSVs
FOLDER = "/Volumes/ssd/work/temp"   # 🔁 change this path
OUTPUT = "/Volumes/ssd/work/ttotal_metadata.csv"

# find all csv files in the folder
csv_files = glob.glob(os.path.join(FOLDER, "*.csv"))

print(f"Found {len(csv_files)} CSV files")

# read and concatenate them (skip header from 2nd file onward)
df_list = [pd.read_csv(f) for f in csv_files]
combined = pd.concat(df_list, ignore_index=True)

# save to one merged CSV
combined.to_csv(OUTPUT, index=False)
print(f"✅ Combined CSV saved to {OUTPUT}")


