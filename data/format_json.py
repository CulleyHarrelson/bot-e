import json
import argparse


def format_json(file_path):
    # Read the JSON file
    with open(file_path, "r") as file:
        data = json.load(file)

    # Write the formatted JSON back to the file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4, sort_keys=True)

    print(f"Formatted JSON written back to {file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Format a JSON file.")
    parser.add_argument(
        "filename", type=str, help="Path to the JSON file to be formatted"
    )

    args = parser.parse_args()
    format_json(args.filename)
