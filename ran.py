import os
import random

# 🔧 Configuration
folder_path = 'skin images/combination_skin'  # ← Change this to your actual folder path
base_name = 'combinationskin'
min_val = 100
max_val = 999

# ✅ Get list of files (ignore directories)
files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

# 🛡️ Safety check to avoid running out of unique numbers
if len(files) > (max_val - min_val + 1):
    raise ValueError("Not enough unique random numbers in the given range.")

# 🎲 Generate unique random numbers
random_numbers = random.sample(range(min_val, max_val + 1), len(files))

# 🔄 Rename files
for filename, rand_num in zip(files, random_numbers):
    ext = os.path.splitext(filename)[1]
    new_name = f"{base_name}_{rand_num}{ext}"
    old_path = os.path.join(folder_path, filename)
    new_path = os.path.join(folder_path, new_name)
    os.rename(old_path, new_path)
    print(f"Renamed: {filename} -> {new_name}")
