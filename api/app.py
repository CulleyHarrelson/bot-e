from flask import Flask, jsonify
import bote
import json
from datetime import datetime

app = Flask(__name__)


def custom_json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    raise TypeError("Type not serializable")


@app.route("/list/<array_of_ids>", methods=["GET"])
def get_rows_by_ids(array_of_ids):
    try:
        # Split the provided array_of_ids into a list of individual ids
        ids_list = array_of_ids.split(",")

        # Get the rows from the database
        rows = bote.get_asks(ids_list)

        # Create a list to hold the JSON objects for each row
        json_rows = []

        for row in rows:
            # Convert the row to a dictionary
            row_dict = {
                "ask_id": row[0],
                "prompt": row[1],
                "title": row[2],
                "added_at": row[3].strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),  # Convert datetime to string
                "ask_status": row[4],
                "hashtags": row[5],
                "embedding": row[6],
                "moderation": row[7],
                "analysis": row[8],
                "system_prompt": row[9],
                "response": row[10],
            }
            json_rows.append(row_dict)

        # Convert the list of dictionaries to JSON
        json_response = json.dumps(json_rows, default=custom_json_serializer)

        # Return the JSON response
        return json_response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
