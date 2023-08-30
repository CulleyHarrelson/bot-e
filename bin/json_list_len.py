import json
import sys

# Check if a filename was provided as an argument
if len(sys.argv) < 2:
    print("Usage: python3 json_list_len.py <path_to_json_file>")
    sys.exit(1)

filename = sys.argv[1]

try:
    with open(filename, "r") as file:
        data = json.load(file)

        # Check if the first element is a list
        if isinstance(data, list):
            print(f"The number of elements in the list is: {len(data)}")
        else:
            print("The first element in the JSON file is not a list.")
except Exception as e:
    print(f"Error reading the file: {e}")
