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
        return bote.get_asks(ids_list)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/similar/<ask_id>", methods=["GET"])
def get_similar(ask_id):
    try:
        # Get the rows from the database
        return bote.similar(ask_id)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
