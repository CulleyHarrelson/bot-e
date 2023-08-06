from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory data store for demonstration purposes
messages = {}
votes = {}
similar_messages = {}


@app.route("/index", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return jsonify({"index": "Welcome to the API!"})
    elif request.method == "POST":
        # Handle POST request (e.g., create a new resource)
        return jsonify({"message": "Resource created"}), 201


@app.route("/msg/<string:ask_id>", methods=["GET"])
def get_message(ask_id):
    message = messages.get(ask_id, None)
    if message is None:
        return jsonify({"error": "Message not found"}), 404
    return jsonify({"message": message})


@app.route("/tos", methods=["GET"])
def terms_of_service():
    return jsonify({"terms_of_service": "Terms of service content here"})


@app.route("/about", methods=["GET"])
def about():
    return jsonify({"about": "About page content here"})


@app.route("/upvote/<string:ask_id>", methods=["PUT"])
def upvote(ask_id):
    votes[ask_id] = votes.get(ask_id, 0) + 1
    return jsonify({"votes": votes[ask_id]})


@app.route("/downvote/<string:ask_id>", methods=["PUT"])
def downvote(ask_id):
    votes[ask_id] = votes.get(ask_id, 0) - 1
    return jsonify({"votes": votes[ask_id]})


@app.route("/similar/<string:ask_id>", methods=["GET"])
def similar(ask_id):
    similar = similar_messages.get(ask_id, [])
    return jsonify({"similar": similar})


@app.route("/similar/<string:ask_id>/exclude/<string:exclude_list>", methods=["GET"])
def similar_exclude(ask_id, exclude_list):
    similar = similar_messages.get(ask_id, [])
    exclude = exclude_list.split(",")
    filtered_similar = [item for item in similar if item not in exclude]
    return jsonify({"similar": filtered_similar})


if __name__ == "__main__":
    app.run(debug=True)
