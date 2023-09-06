from flask import Flask, jsonify, request
import bote
from datetime import datetime
import json
from flask_cors import CORS

app = Flask(__name__)

CORS(app, origins=["https://bot-e.com", "http://localhost:3000"])


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


@app.route("/search/<search_for>", methods=["GET"])
def search(search_for):
    try:
        # Split the provided array_of_ids into a list of individual ids

        # Get the rows from the database
        return bote.search(search_for)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/question/<question_id>", methods=["GET"])
def get_question_by_id(question_id):
    try:
        # Get the rows from the database
        question = bote.simplified_question(question_id)
        return question

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/next_question", methods=["POST"])
def next_question():
    """
    this route is for the navigation on the question page. data is
    saved to question_vote table and the embeddings is used for a
    proximity search, or a random question is returned if they hit
    the random button
    """
    try:
        direction = request.form.get("direction")
        question_id = request.form.get("question_id")
        session_id = request.form.get("session_id")

        if direction == "random":
            random_question = bote.random_question()
            return jsonify({"question_id": random_question.get("question_id")})
        else:
            if not question_id:
                return jsonify({"error": "question_id is required."}), 400
            if not session_id:
                return jsonify({"error": "session_id is required."}), 400
            next_question_data = bote.next_question(question_id, session_id, direction)
            return jsonify({"question_id": next_question_data.get("question_id")})

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
