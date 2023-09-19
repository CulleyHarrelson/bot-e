from aiohttp import web
import asyncpg
import bote
from datetime import datetime
from dateutil.parser import isoparse
import re
from html import unescape
import asyncio

# import json

import logging

logging.basicConfig(level=logging.DEBUG)


async def contains_html(input_string):
    cleaned_string = unescape(input_string)
    html_pattern = re.compile(r"<[^>]+>")
    return bool(html_pattern.search(cleaned_string))


async def contains_url(input_string):
    url_pattern = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
    matches = url_pattern.findall(input_string)
    return bool(matches)


async def get_rows_by_ids(request):
    # Implementation here
    pass


async def trending(request):
    # Implementation here
    pass


async def get_question_comments_id(request):
    try:
        # Get the rows from the database
        question_id = request.match_info["question_id"]
        comments = await bote.question_comments(question_id)
        if not comments:
            # Return an empty JSON array if no comments are found
            return web.json_response([])

        return web.json_response(comments)

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def get_question_by_id(request):
    try:
        # Get the rows from the database
        question_id = request.match_info["question_id"]
        # logging.debug(f"Fetching question with ID: {question_id}")
        question = await bote.simplified_question(question_id)

        response = web.json_response(question)
        response.headers["Content-Type"] = "application/json"

        return response

    except Exception as e:
        # logging.exception("Error occurred while processing the request.")
        return web.json_response({"error": str(e)}, status=500)


async def next_question(request):
    """
    this route is for the navigation on the question page. data is
    saved to question_vote table and the embeddings is used for a
    proximity search, or a random question is returned if they hit
    the random button.  Functionality could be split into vote and navigation
    methods
    """
    try:
        data = await request.json()  # Extract JSON data from the request
        direction = data["direction"]
        question_id = data["question_id"]
        session_id = data["session_id"]

        if direction == "random":
            random_question = await bote.random_question()
            return web.json_response(
                {"question_id": random_question.get("question_id")}
            )
        else:
            if not question_id:
                return web.json_response(
                    {"error": "question_id is required."}, status=400
                )
            if not session_id:
                return web.json_response(
                    {"error": "session_id is required."}, status=400
                )
            next_question_data = await bote.next_question(
                question_id, session_id, direction
            )  # Assuming bote.next_question is asynchronous
            return web.json_response(
                {"question_id": next_question_data.get("question_id")}
            )

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def post_question(request):
    try:
        data = request.json()
        if "question" not in data or not data["question"]:
            return web.json_response({"error": "question is required."}, status=400)

        question = data["question"]

        logging.debug(f"new question: {question}")

        result = await bote.post_question(question)
        return web.json_response(result)

    except Exception as e:
        logging.exception("Error occurred while processing the request.")
        return web.json_response({"error": str(e)}), 500


async def add_comment(request):
    # Implementation here
    pass


async def init_app():
    app = web.Application()
    # Add routes here
    app.router.add_get("/list/{array_of_ids}", get_rows_by_ids)
    app.router.add_get("/trending/{start_date}", trending)
    app.router.add_get("/comments/{question_id}", get_question_comments_id)
    app.router.add_get("/question/{question_id}", get_question_by_id)
    app.router.add_post("/next_question", next_question)
    app.router.add_post("/ask", post_question)
    app.router.add_post("/add_comment", add_comment)
    return app


loop = asyncio.get_event_loop()
app = loop.run_until_complete(init_app())
