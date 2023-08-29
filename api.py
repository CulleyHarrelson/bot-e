from flask import Flask, jsonify, request
import bote
from datetime import datetime

# import logging
# logging.basicConfig(level=logging.DEBUG)


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
        return bote.get_questions(ids_list)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/question/<question_id>", methods=["GET"])
def get_question_by_id(question_id):
    try:
        # Get the rows from the database
        return bote.get_question(question_id)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/similar/<question_id>", methods=["GET"])
def get_similar(question_id):
    try:
        # Get the rows from the database
        return bote.similar(question_id)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/ask", methods=["POST"])
def post_question():
    try:
        # Get the question text from the request's JSON body
        data = request.get_json()

        # Check if the "question" field is present and not empty
        if "question" not in data or not data["question"]:
            return jsonify({"error": "question is required."}), 400

        question = data["question"]

        # Process the question using bote or any other necessary method
        question = bote.post_question(question)
        return question

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=6464)
