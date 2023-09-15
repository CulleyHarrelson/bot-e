from flask import Flask, jsonify, request
import bote
from datetime import datetime
from dateutil.parser import isoparse
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
from html import unescape
import re

app = Flask(__name__)

CORS(
    app,
    origins=["https://bot-e.com", "http://localhost:3000", "http://snowball.bot-e.com"],
)


def contains_html(input_string):
    cleaned_string = unescape(input_string)

    html_pattern = re.compile(r"<[^>]+>")
    return bool(html_pattern.search(cleaned_string))


def contains_url(input_string):
    url_pattern = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

    matches = url_pattern.findall(input_string)

    return bool(matches)


def custom_json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    raise TypeError("Type not serializable")


# this isn't called yet
@app.route("/list/<array_of_ids>", methods=["GET"])
def get_rows_by_ids(array_of_ids):
    try:
        ids_list = array_of_ids.split(",")

        return bote.get_questions(ids_list)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/trending/<start_date>", methods=["GET"])
def trending(start_date):
    try:
        try:
            start_date_parsed = isoparse(start_date)
        except ValueError:
            raise BadRequest(
                "Invalid date format. Please use ISO 8601 format (YYYY-MM-DD)."
            )
        if not isinstance(start_date_parsed, datetime):
            raise ValueError("Invalid date format")

        if not isinstance(start_date_parsed, datetime):
            raise ValueError("Invalid date format")

        # Get the rows from the database
        return bote.trending(start_date)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/comments/<question_id>", methods=["GET"])
def get_question_comments_id(question_id):
    try:
        # Get the rows from the database
        comments = bote.question_comments(question_id)
        return comments

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/question/<question_id>", methods=["GET"])
def get_question_by_id(question_id):
    try:
        # Get the rows from the database
        question = bote.simplified_question(question_id)

        response = jsonify(question)
        response.headers["Content-Type"] = "application/json"

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/next_question", methods=["POST"])
def next_question():
    """
    this route is for the navigation on the question page. data is
    saved to question_vote table and the embeddings is used for a
    proximity search, or a random question is returned if they hit
    the random button.  Functionality could be split into vote and navigation
    methods
    """
    try:
        direction = request.json["direction"]
        question_id = request.json["question_id"]
        session_id = request.json["session_id"]

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
        data = request.get_json()

        if "question" not in data or not data["question"]:
            return jsonify({"error": "question is required."}), 400

        question = data["question"]

        question = bote.post_question(question)
        return question

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/add_comment", methods=["POST"])
def add_comment():
    try:
        data = request.get_json()

        if "question_id" not in data or not data["question_id"]:
            return jsonify({"error": "question_id is required."}), 400

        question_id = data["question_id"]

        if "comment" not in data or not data["comment"]:
            return jsonify({"error": "comment is required."}), 400

        if contains_html(data["comment"]) or contains_url(data["comment"]):
            return (
                jsonify({"error": "comments with html and links are not processed."}),
                400,
            )

        comment = data["comment"]

        if "session_id" not in data or not data["session_id"]:
            return jsonify({"error": "session_id is required."}), 400

        session_id = data["session_id"]

        # add this in to enable replies
        # parent_comment_id = data["parent_comment_id"]

        # Process the question using bote or any other necessary method
        comment = bote.add_comment(question_id, comment, session_id)

        return comment

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=6464)
