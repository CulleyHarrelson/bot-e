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

log = bote.setup_logging(level=logging.DEBUG)


async def contains_html(input_string):
    cleaned_string = unescape(input_string)
    html_pattern = re.compile(r"<[^>]+>")
    return bool(html_pattern.search(cleaned_string))


async def contains_url(input_string):
    url_pattern = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
    matches = url_pattern.findall(input_string)
    return bool(matches)


async def search(request):
    try:
        search_for = request.match_info["search_for"]

        if not search_for:
            raise web.HTTPBadRequest(text="Missing search phrase parameter.")

        result = await bote.search(search_for)

        return web.json_response(result)

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


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
        log.debug(f"Fetching question with ID: {question_id}")
        question = await bote.simplified_question(question_id)
        if question:
            log.debug("found question")
        else:
            log.debug(f"question not found: {question_id}")
        response = web.json_response(question)
        response.headers["Content-Type"] = "application/json"

        return response

    except Exception as e:
        if question_id:
            log.warn(f"Error occurred while getting data for question {question_id}")
        else:
            log.critical("no question id to look up in the database.")
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
        log.debug(question_id)

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
        log.debug("in post question here ")
        data = await request.json()
        log.debug("begging post question function in api script")
        if "question" not in data or not data["question"]:
            return web.json_response({"error": "question is required."}, status=400)
        if "session_id" not in data or not data["session_id"]:
            return web.json_response({"error": "session_id is required."}, status=400)

        question = data["question"]
        session_id = data["session_id"]

        logging.debug(f"new question for session: {session_id}")

        result = await bote.post_question(question, session_id)
        return web.json_response(result)

    except Exception as e:
        return web.json_response({"error": str(e)}), 500


async def respond(request):
    try:
        log.debug("in respond")
        data = await request.json()
        if "question_id" not in data or not data["question_id"]:
            return web.json_response({"error": "question_id is required."}, status=400)

        question_id = data["question_id"]

        logging.debug(f"responding: {question_id}")

        result = await bote.respond(question_id)
        return web.json_response(result)

    except Exception as e:
        return web.json_response({"error": str(e)}), 500


async def add_comment(request):
    try:
        data = await request.json()
        question_id = data.get("question_id")
        session_id = data.get("session_id")
        comment = data.get("comment")

        if not question_id or not session_id or not comment:
            return web.json_response(
                {"error": "question_id, session_id, and comment are required."},
                status=400,
            )

        if not bote.validate_key(question_id):
            return web.json_response({"error": "Invalid question_id."}, status=400)

        conn = await db_connect2()  # Use db_connect2 to establish a database connection

        try:
            async with conn.transaction():
                result_tuple = await conn.fetchval(
                    "select * from insert_question_comment ($1, $2, $3)",
                    (question_id, session_id, comment),
                )

            return web.json_response({"result": result_tuple})
        finally:
            await conn.close()
    except Exception as e:
        error_message = str(e)
        return web.json_response({"error": error_message}, status=500)


async def init_app():
    app = web.Application()
    # trending is not currently functional
    # app.router.add_get("/trending/{start_date}", trending)
    app.router.add_get("/search/{search_for}", search)
    app.router.add_get("/comments/{question_id}", get_question_comments_id)
    app.router.add_get("/question/{question_id}", get_question_by_id)
    app.router.add_post("/next_question", next_question)
    app.router.add_post("/ask", post_question)
    app.router.add_post("/respond", respond)
    app.router.add_post("/add_comment", add_comment)
    return app


loop = asyncio.get_event_loop()
app = loop.run_until_complete(init_app())

# tasync def trending(request):
#    try:
#        start_date = request.query.get("start_date")
#
#        if not start_date:
#            raise web.HTTPBadRequest(text="Missing 'start_date' query parameter.")
#
#        try:
#            start_date_parsed = isoparse(start_date)
#        except ValueError:
#            raise web.HTTPBadRequest(
#                text="Invalid date format. Please use ISO 8601 format (YYYY-MM-DD)."
#            )
#
#        if not isinstance(start_date_parsed, datetime):
#            raise ValueError("Invalid date format")
#
#        result = await bote.trending(start_date_parsed)
#
#        return web.json_response(result)
#
#    except Exception as e:
#        return web.json_response({"error": str(e)}, status=500)
