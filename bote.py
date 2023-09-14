#!/usr/local/bin/python

import psycopg2
import psycopg2.extensions
from psycopg2.extras import DictCursor

import requests
import openai
import json
from datetime import datetime
import os

import io
import warnings
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from config import OPENAI_API_KEY

os.environ["STABILITY_HOST"] = "grpc.stability.ai:443"

openai.api_key = OPENAI_API_KEY


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def custom_json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    raise TypeError("Type not serializable")


def db_connect():
    conn = psycopg2.connect(
        host="localhost",
        dbname="bot-e",
        port="5432",
    )
    cursor = conn.cursor(cursor_factory=DictCursor)
    return conn, cursor


def new_question(conn, cursor, question):
    question = question.strip()
    if len(question) < 1:
        return {}
    # insert a new question record and get back the question_id
    cursor.execute(
        "INSERT INTO question (question) VALUES (%s) RETURNING *", (question,)
    )
    conn.commit()
    result_tuple = cursor.fetchone()

    column_names = [desc[0] for desc in cursor.description]
    result_dict = dict(zip(column_names, result_tuple))

    return result_dict


def next_embedding(cursor):
    # this returns an question record that is in need of embedding
    cursor.execute(
        "SELECT * FROM question WHERE embedding IS NULL ORDER BY added_at LIMIT 1;"
    )
    return cursor.fetchone()


def next_moderation(cursor):
    # this returns an question record that is in need of moderation
    cursor.execute(
        "SELECT * FROM question WHERE moderation IS NULL ORDER BY added_at LIMIT 1;"
    )
    return cursor.fetchone()


def answer_next(cursor):
    # this returns an question record that is in need of moderation
    cursor.execute(
        "SELECT * FROM question WHERE answer IS NULL ORDER BY added_at ASC LIMIT 1;"
    )

    question = cursor.fetchone()
    if question:
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, question))
        return data
    else:
        return None


def respond():
    conn, cursor = db_connect()
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    question = answer_next(cursor)
    cursor.execute("LISTEN new_question;")

    while True:
        if not question:
            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                if notify.channel == "new_question":
                    # question_id = notify.payload
                    question = answer_next(cursor)
                    break
        else:
            respond_to_question(conn, cursor, question)
            question = answer_next(cursor)


def post_question(question):
    conn, cursor = db_connect()
    question = new_question(conn, cursor, question)
    embed_question(conn, cursor, question)
    moderate_question(conn, cursor, question)

    cursor.close()
    conn.close()
    return question


def add_comment(question_id, comment, session_id):
    try:
        if not validate_key(question_id):
            return json.dumps({"error": "question_id is required."})

        conn, cursor = db_connect()
        cursor.execute(
            "select * from insert_question_comment (%s, %s, %s)",
            (
                question_id,
                session_id,
                comment,
            ),
        )
        conn.commit()
        result_tuple = cursor.fetchone()
        # moderate_question(conn, cursor, question)

        cursor.close()
        conn.close()
        return result_tuple
    except psycopg2.Error as e:
        error_message = str(e)
        return json.dumps({"error": error_message})


def moderation_api(input_text):
    response = openai.Moderation.create(input=input_text)
    return response


def validate_key(key):
    # Define the set of allowed characters
    allowed_chars = set(
        "-_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    )

    # Check if the string is 11 characters long
    if len(key) != 11:
        return False

    # Check if the first or last character is _ or -
    if key[0] in "-_" or key[-1] in "-_":
        return False

    # Check if all characters are in the allowed set
    for char in key:
        if char not in allowed_chars:
            return False

    # If all tests pass, return True
    return True


def search(search_for):
    conn, cursor = db_connect()

    cursor.execute(
        "select question_id, question, answer, full_image_url(image_url) AS image_url, media, title, description, added_at from search(%s)",
        (search_for,),
    )
    questions = cursor.fetchall()
    # Convert the rows to a list of dictionaries
    columns = [desc[0] for desc in cursor.description]
    data = [dict(zip(columns, row)) for row in questions]

    cursor.close()
    conn.close()
    json_response = json.dumps(data, default=custom_json_serializer)
    return json_response


def trending(start_date):
    conn, cursor = db_connect()

    # third parameter row_limit not used below
    cursor.execute(
        "select * from get_top_upvotes(%s)",
        (start_date,),
    )
    questions = cursor.fetchall()
    # Convert the rows to a list of dictionaries
    columns = [desc[0] for desc in cursor.description]
    data = [dict(zip(columns, row)) for row in questions]

    cursor.close()
    conn.close()
    json_response = json.dumps(data, default=custom_json_serializer)
    return json_response


def get_questions(question_ids):
    conn, cursor = db_connect()

    # Filter out invalid question_ids
    valid_question_ids = [
        question_id for question_id in question_ids if validate_key(question_id)
    ]

    cursor.execute(
        "select question_id, question, answer, full_image_url(image_url) AS image_url, media, title, description, added_at from question where question_id = ANY(%s)",
        (valid_question_ids,),
    )
    questions = cursor.fetchall()
    # Convert the rows to a list of dictionaries
    columns = [desc[0] for desc in cursor.description]
    data = [dict(zip(columns, row)) for row in questions]

    cursor.close()
    conn.close()
    json_response = json.dumps(data, default=custom_json_serializer)
    return json_response


def get_question(question_id, return_json=True):
    conn, cursor = db_connect()

    if not validate_key(question_id):
        return json.dumps([])

    cursor.execute(
        "SELECT * FROM question WHERE question_id = %s",
        (question_id,),
    )
    question = cursor.fetchone()
    cursor.close()
    conn.close()

    if not question:
        return json.dumps([])

    columns = [desc[0] for desc in cursor.description]
    data = dict(zip(columns, question))

    if return_json:
        json_data = json.dumps(data, cls=DateTimeEncoder)
        return json_data
    else:
        return data


def simplified_question(question_id):
    """
    suface limited data to api
    """
    conn, cursor = db_connect()

    if not validate_key(question_id):
        return json.dumps([])

    cursor.execute(
        "SELECT question_id, question, answer, full_image_url(image_url) AS image_url, media, title, description, added_at FROM question WHERE question_id = %s",
        (question_id,),
    )
    question = cursor.fetchone()
    cursor.close()
    conn.close()

    if not question:
        return json.dumps([])

    columns = [desc[0] for desc in cursor.description]
    data = dict(zip(columns, question))
    return data


def question_comments(question_id):
    # TODO: moderate this
    conn, cursor = db_connect()

    if not validate_key(question_id):
        return json.dumps([])

    cursor.execute(
        "SELECT question_id, comment, session_id, parent_comment_id, comment_id, TO_CHAR(added_at, 'YYYY-MM-DD HH:MI AM') AS added_at FROM question_comment WHERE question_id = %s order by added_at desc limit 100",
        (question_id,),
    )

    comments = cursor.fetchall()
    # Convert the rows to a list of dictionaries
    columns = [desc[0] for desc in cursor.description]
    data = [dict(zip(columns, row)) for row in comments]

    cursor.close()
    conn.close()
    json_response = json.dumps(data, default=custom_json_serializer)
    return json_response


def random_question():
    conn, cursor = db_connect()

    cursor.execute(
        "SELECT * FROM question ORDER BY RANDOM() LIMIT 1",
    )
    question = cursor.fetchone()
    cursor.close()
    conn.close()

    if not question:
        return json.dumps([])

    columns = [desc[0] for desc in cursor.description]
    data = dict(zip(columns, question))

    return data


def next_question(question_id, session_id, direction):
    conn, cursor = db_connect()

    # Filter out invalid question_ids
    if not validate_key(question_id):
        return "[]"

    if direction == "down":
        similarity = False
    else:
        similarity = True

    cursor.execute(
        "select * from proximal_question(%s, %s, %s)",
        (question_id, session_id, similarity),
    )

    question = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()

    if not question:
        return json.dumps([])

    columns = [desc[0] for desc in cursor.description]
    data = dict(zip(columns, question))

    return data


def moderate_questions():
    conn, cursor = db_connect()
    while True:
        question = next_moderation(cursor)
        if question is None:
            break

        moderation = moderation_api(question["question"])
        cursor.execute(
            "update question set moderation = %s where question_id = %s",
            (json.dumps(moderation), question["question_id"]),
        )
        conn.commit()
        # time.sleep(0.8)
    conn.close()
    cursor.close()


def embedding_api(input_text):
    response = openai.Embedding.create(input=input_text, model="text-embedding-ada-002")
    return response["data"][0]["embedding"]


def embed_question(conn, cursor, question):
    embedding = embedding_api(question["question"])
    cursor.execute(
        "update question set embedding = %s where question_id = %s",
        (embedding, question["question_id"]),
    )
    conn.commit()


def moderate_question(conn, cursor, question):
    moderation = moderation_api(question["question"])
    cursor.execute(
        "update question set moderation = %s where question_id = %s",
        (json.dumps(moderation), question["question_id"]),
    )
    conn.commit()


def embed_questions():
    conn, cursor = db_connect()
    while True:
        question = next_embedding(cursor)
        if question is None:
            break

        embedding = embedding_api(question["question"])
        cursor.execute(
            "update question set embedding = %s where question_id = %s",
            (embedding, question["question_id"]),
        )
        conn.commit()
        # time.sleep(0.8)
    conn.close()
    cursor.close()


def respond_to_question(conn, cursor, data):
    user_message = data["question"]
    with open("data/system_prompt.txt", "r") as file:
        system_prompt = file.read()

    question_id = data["question_id"]

    system_message = f"{system_prompt}"

    messages = [
        {
            "role": "system",
            "content": f"{system_message}",
        },
        {
            "role": "user",
            "content": f"{user_message}",
        },
    ]
    completion = openai.ChatCompletion.create(
        # model="gpt-4",
        model="gpt-3.5-turbo",
        messages=messages,
    )

    messages.append(completion["choices"][0]["message"])

    response_message = completion["choices"][0]["message"]["content"]
    lines = response_message.split("\n", 1)
    title_line = lines[0]
    rest_of_answer = lines[1]

    # if this fails, the model did not return a title
    try:
        title = title_line.split(":", 1)[1].strip()
    except IndexError:
        title = ""
        rest_of_answer = response_message

    cursor.execute(
        "update question set answer = %s, system_prompt = %s, title = %s where question_id = %s",
        (
            json.dumps(rest_of_answer),
            system_message,
            title,
            question_id,
        ),
    )
    conn.commit()
    with open("data/question_functions.json", "r") as file:
        functions = json.load(file)

    function_completion = openai.ChatCompletion.create(
        # model="gpt-4",
        model="gpt-3.5-turbo",
        messages=messages,
        functions=functions,
        function_call={"name": "extract_data"},
    )
    function_message = function_completion["choices"][0]["message"]

    if function_message.get("function_call"):
        function_response = json.loads(function_message["function_call"]["arguments"])
        description = function_response["description"]
        media = function_response["media"]
        # if len(media) > 0:
        #     for record in media:
        #         videos = search_youtube_videos(record["title"])
        #         for video in videos:
        #             record["videoId"] = video["videoId"]
        #             record["thumbnailUrl"] = video["thumbnailUrl"]
        #             record["videoTitle"] = video["title"]

        if len(title) == 0:
            # if there was a previous title failure....
            title = function_response["title"]

        try:
            image_url = stability_image(title, question_id)
        except Exception as e:
            image_url = openai_image(title, question_id)
        cursor.execute(
            "update question set title = %s, description = %s, image_url = %s, media = %s where question_id = %s",
            (
                title,
                description,
                image_url,
                json.dumps(media),
                question_id,
            ),
        )
        conn.commit()

    return get_question(question_id)


def openai_image(title, question_id):
    try:
        response = openai.Image.create(
            prompt=f"Generate an abstract image representing: {title}",
            n=1,
            size="256x256",
        )
        image_url = response["data"][0]["url"]
        base_dir = os.path.dirname(os.path.abspath(__file__))
        images_dir = os.path.join(base_dir, "images")
        questions_dir = os.path.join(images_dir, "questions")
        folder_character = question_id[0].lower()
        question_subfolder = os.path.join(questions_dir, folder_character)
        os.makedirs(question_subfolder, exist_ok=True)
        image_data = requests.get(image_url).content
        image_filename = os.path.join(question_subfolder, f"{question_id}.png")
        with open(image_filename, "wb") as image_file:
            image_file.write(image_data)
        return f"/images/questions/{folder_character}/{question_id}.png"
    except openai.error.InvalidRequestError:
        image_url = ""
    return image_url


def stability_image(title, question_id):
    stability_api = client.StabilityInference(
        key=os.environ["STABILITY_KEY"],
        verbose=True,  # Print debug messages.
        engine="stable-diffusion-xl-1024-v1-0",
    )

    answers = stability_api.generate(
        prompt=f"using mostly dark tones create an image that will make people curious about this title: '{title}'. ",
        seed=4253978046,
        steps=30,
        cfg_scale=7.0,
        width=512,
        height=512,
        samples=1,
        sampler=generation.SAMPLER_K_DPMPP_2M,
    )

    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                raise ValueError(
                    "Your request activated the API's safety filters and could not be processed."
                )
            if artifact.type == generation.ARTIFACT_IMAGE:
                img = Image.open(io.BytesIO(artifact.binary))
                base_dir = os.path.dirname(os.path.abspath(__file__))
                images_dir = os.path.join(base_dir, "images")
                questions_dir = os.path.join(images_dir, "questions")
                folder_character = question_id[0].lower()
                question_subfolder = os.path.join(questions_dir, folder_character)
                os.makedirs(question_subfolder, exist_ok=True)
                image_filename = os.path.join(question_subfolder, f"{question_id}.png")

                img.save(image_filename)
                return f"/images/questions/{folder_character}/{question_id}.png"

    return ""


if __name__ == "__main__":
    respond()
    # embed_questions()
    # conn, cursor = db_connect()
    # question = get_question("KiV4OnQED4V", return_json=False)
    # response = respond_to_question(conn, cursor, question)


# def search_youtube_videos(search_phrase):
#     youtube = googleapiclient.discovery.build(
#         "youtube", "v3", developerKey=os.environ["YOUTUBE_DATA_API_KEY"]
#     )
#     try:
#         # Perform the YouTube search
#         request = youtube.search().list(
#             q=search_phrase, type="video", part="id,snippet", maxResults=1
#         )
#
#         response = request.execute()
#
#         # Construct the list of dictionaries
#         results = []
#         for item in response.get("items", []):
#             result = {
#                 "videoId": item["id"]["videoId"],
#                 "thumbnailUrl": item["snippet"]["thumbnails"]["default"]["url"],
#                 "title": item["snippet"]["title"],
#             }
#             results.append(result)
#
#         return results
#     except HttpError as e:
#         print(f"An HTTP error occurred: {e}")
#         return []


# import googleapiclient.discovery
# from googleapiclient.errors import HttpError
