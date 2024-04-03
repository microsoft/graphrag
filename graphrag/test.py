import os
import json

base_dir = "/Users/christrevino/ws/pipeline/indexing_run_3/cache/community_reporting/"

file_list = os.listdir(base_dir)
print(file_list)

num_good = 0
num_bad = 0
for file in file_list:
    file_path = os.path.join(base_dir, file)
    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
        except json.decoder.JSONDecodeError:
            print(f"Error in file: {file}")
            num_bad += 1
        except UnicodeDecodeError:
            print(f"Error in file: {file}")
            num_bad += 1
        else:
            num_good += 1

print(f"Good: {num_good}, Bad: {num_bad}")