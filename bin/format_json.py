import json
import argparse


def format_json(file_path):
    # Read the JSON file
    with open(file_path, "r") as file:
        data = json.load(file)

    print(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Format a JSON file.")
    parser.add_argument(
        "filename", type=str, help="Path to the JSON file to be formatted"
    )

    args = parser.parse_args()
    format_json(args.filename)
