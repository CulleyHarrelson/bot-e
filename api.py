from aiohttp import web
import asyncpg
import bote
from datetime import datetime
from dateutil.parser import isoparse
import re
from html import unescape
import asyncio

# import aiohttp_cors


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
        bote.debug(f"Fetching question with ID: {question_id}")
        question = await bote.simplified_question(question_id)
        response = web.json_response(question)
        response.headers["Content-Type"] = "application/json"

        return response

    except Exception as e:
        if question_id:
            bote.warn(f"Error occurred while getting data for question {question_id}")
        else:
            bote.critical("no question id to look up in the database.")
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
        data = await request.json()
        direction = data["direction"]
        if direction == "random":
            bote.debug("random")
            random_question = await bote.random_question()
            return web.json_response(
                {"question_id": random_question.get("question_id")}
            )
        else:
            question_id = data["question_id"]
            session_id = data["session_id"]
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
        bote.debug("in post question here ")
        data = await request.json()
        bote.debug("begging post question function in api script")
        if "question" not in data or not data["question"]:
            return web.json_response({"error": "question is required."}, status=400)
        if "session_id" not in data or not data["session_id"]:
            return web.json_response({"error": "session_id is required."}, status=400)

        question = data["question"]
        session_id = data["session_id"]

        bote.debug(f"new question for session: {session_id}")

        result = await bote.post_question(question, session_id)
        return web.json_response(result)

    except Exception as e:
        return web.json_response({"error": str(e)}), 500


async def respond(request):
    try:
        data = await request.json()
        if "question_id" not in data or not data["question_id"]:
            return web.json_response({"error": "question_id is required."}, status=400)

        question_id = data["question_id"]

        if "enrich" in data:
            bote.debug(f"respond - obtaining enrich lock: {question_id}")
            lock = await bote.row_lock(f"E-{question_id}")

            bote.debug(lock)
            if lock:
                bote.debug(f"LOCKED enriching question call: {question_id}")
                result = await bote.enrich_question(question_id)
                return web.json_response(result)
            else:
                bote.debug(
                    f"FAILED TO ENRICH QUESTION: enrich api call locked: {question_id}"
                )
        else:
            bote.debug(f"respond - obtaining question lock: {question_id}")
            lock = await bote.row_lock(f"A-{question_id}")
            bote.debug(lock)
            if lock:
                bote.debug(f"LOCKED - respond to question: {question_id}")
                result = await bote.respond(question_id)
                return web.json_response(result)
            else:
                bote.debug(
                    f"FAILED TO RESPOND TO QUESTION: respond api call locked: {question_id}"
                )

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

        conn = await bote.db_connect2()

        try:
            async with conn.transaction():
                result_tuple = await conn.fetchval(
                    "select * from insert_question_comment ($1, $2, $3)",
                    question_id,
                    session_id,
                    comment,
                )
            return web.json_response({"success": True}, status=200)
        finally:
            await conn.close()
    except Exception as e:
        bote.debug(e)
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


# cors = aiohttp_cors.setup(app)
#
# resource = cors.add(app.router.add_resource("/respond"))
# route = cors.add(
#    resource.add_route("POST", respond),
#    {
#        "*": aiohttp_cors.ResourceOptions(
#            allow_credentials=True,  # Allow credentials (cookies, authentication)
#            expose_headers=("X-Custom-Header",),  # Expose custom headers
#            allow_headers=(
#                "Content-Type",
#                "Authorization",
#            ),  # Allow headers in requests
#            max_age=3600,  # Set the maximum age for preflight requests (in seconds)
#        )
#    },
# )


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
