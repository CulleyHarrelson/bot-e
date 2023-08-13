# 3408
import psycopg2

# DictCursor returns data as dictionaries instead of tuples
from psycopg2.extras import DictCursor
import os
import openai
import time
import json
import random
from datetime import datetime

from config import OPENAI_API_KEY, POSTGRESQL_KEY


openai.api_key = OPENAI_API_KEY
pg_password = POSTGRESQL_KEY
# openai.api_key = os.getenv("OPENAI_API_KEY")
# pg_password = os.getenv("POSTGRESQL_KEY")


def custom_json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    raise TypeError("Type not serializable")


def db_connect():
    conn = psycopg2.connect(
        host="bot-e.cluster-chki9sxssda8.us-east-2.rds.amazonaws.com",
        user="postgres",
        password=f"{pg_password}",
        port="5432",
    )
    cursor = conn.cursor(cursor_factory=DictCursor)
    return conn, cursor


def next_embedding(cursor):
    # this returns an ask record that is in need of embedding
    cursor.execute("SELECT * FROM next_embedding()")
    return cursor.fetchone()


def next_moderation(cursor):
    # this returns an ask record that is in need of moderation
    cursor.execute("SELECT * FROM next_moderation()")
    return cursor.fetchone()


def next_analysis(cursor):
    # this returns an ask record that is in need of analysis
    cursor.execute("SELECT * FROM next_analysis()")
    return cursor.fetchone()


def random_ask(cursor):
    # this returns an ask record that is in need of analysis
    cursor.execute("SELECT * FROM ask order by RANDOM() limit 1")
    return cursor.fetchone()


def new_ask(conn, cursor, prompt):
    prompt = prompt.strip()
    if len(prompt) < 1:
        return {}
    # insert a new ask record and get back the ask_id
    cursor.execute("SELECT * FROM new_ask(%s)", (prompt,))
    conn.commit()
    return cursor.fetchone()


def post_ask(prompt):
    conn, cursor = db_connect()
    ask = new_ask(conn, cursor, prompt)
    embed_ask(conn, cursor, ask)
    moderate_ask(conn, cursor, ask)
    response = respond_to_ask(conn, cursor, ask)
    cursor.close()
    conn.close()
    return response


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


def get_asks(ask_ids):
    conn, cursor = db_connect()

    # Filter out invalid ask_ids
    valid_ask_ids = [ask_id for ask_id in ask_ids if validate_key(ask_id)]

    cursor.execute(
        "select * from ask where ask_id = ANY(%s)",
        (valid_ask_ids,),
    )
    asks = cursor.fetchall()
    # Convert the rows to a list of dictionaries
    columns = [desc[0] for desc in cursor.description]
    data = [dict(zip(columns, row)) for row in asks]

    cursor.close()
    conn.close()
    json_response = json.dumps(data, default=custom_json_serializer)
    # json_response = json.dumps(data)
    return json_response


def get_ask(ask_id):
    # Call get_asks with a list containing a single ask_id
    asks = get_asks([ask_id])

    # If get_asks returned a non-empty list, return the first element
    if asks:
        return asks[0]

    # Otherwise, return None
    return None


def similar(ask_id):
    conn, cursor = db_connect()

    # Filter out invalid ask_ids
    if not validate_key(ask_id):
        return "[]"

    cursor.execute(
        "select * from similar(%s)",
        (ask_id,),
    )
    asks = cursor.fetchall()
    # Convert the rows to a list of dictionaries
    columns = [desc[0] for desc in cursor.description]
    data = [dict(zip(columns, row)) for row in asks]

    cursor.close()
    conn.close()

    # Convert the list of dictionaries to JSON
    json_response = json.dumps(data, default=custom_json_serializer)
    return json_response


def moderate_asks():
    conn, cursor = db_connect()
    while True:
        ask = next_moderation(cursor)
        if ask is None:
            break

        moderation = moderation_api(ask["prompt"])
        cursor.execute(
            "update ask set moderation = %s where ask_id = %s",
            (json.dumps(moderation), ask["ask_id"]),
        )
        conn.commit()
        # time.sleep(0.8)
    conn.close()
    cursor.close()


def embedding_api(input_text):
    response = openai.Embedding.create(input=input_text, model="text-embedding-ada-002")
    return response["data"][0]["embedding"]


def embed_ask(conn, cursor, ask):
    embedding = embedding_api(ask["prompt"])
    cursor.execute(
        "update ask set embedding = %s where ask_id = %s",
        (embedding, ask["ask_id"]),
    )
    conn.commit()


def moderate_ask(conn, cursor, ask):
    moderation = moderation_api(ask["prompt"])
    cursor.execute(
        "update ask set moderation = %s where ask_id = %s",
        (json.dumps(moderation), ask["ask_id"]),
    )
    conn.commit()


def embed_asks():
    conn, cursor = db_connect()
    while True:
        ask = next_embedding(cursor)
        if ask is None:
            break

        embedding = embedding_api(ask["prompt"])
        cursor.execute(
            "update ask set embedding = %s where ask_id = %s",
            (embedding, ask["ask_id"]),
        )
        conn.commit()
        # time.sleep(0.8)
    conn.close()
    cursor.close()


def content_compliance(ask):
    return ask


def advise(ask):
    return ask


def respond_to_ask(conn, cursor, ask):
    user_message = ask["prompt"]
    start_time = time.time()
    with open("db/prompt_bot-e_main.txt", "r") as file:
        system_message = file.read()

    analysis_json = analysis_api(user_message)
    analysis_usage = analysis_json["usage"]["total_tokens"]
    response_message = analysis_json["choices"][0]["message"]

    if response_message.get("function_call"):
        analysis = response_message["function_call"]["arguments"]
    else:
        analysis = '{"advice_type": "API_FAILURE"}'

    completion = openai.ChatCompletion.create(
        model="gpt-4",
        # model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": f"{system_message}",
            },
            {
                "role": "user",
                "content": f"{user_message}",
            },
        ],
    )

    response_message = completion["choices"][0]["message"]["content"]
    response_usage = completion["usage"]["total_tokens"]
    cursor.execute(
        "update ask set response = %s, system_prompt = %s, analysis = %s where ask_id = %s",
        (
            json.dumps(response_message),
            system_message,
            json.dumps(analysis),
            ask["ask_id"],
        ),
    )
    conn.commit()
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(
        f"Ask ID: {ask['ask_id']}, Analysis Usage: {analysis_usage}, Response Usage: {response_usage}, Time taken: {elapsed_time} seconds"
    )
    return True
    # return completion


def analysis_api(user_message):
    with open("db/analysis_functions.json", "r") as file:
        functions = json.load(file)
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        # model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Assess the author of the following message.  It should be a message asking for advice.",
            },
            {
                "role": "user",
                "content": f"{user_message}",
            },
        ],
        functions=functions,
        function_call={"name": "extract_data"},
    )
    return completion


def analyze_asks():
    conn, cursor = db_connect()
    while True:
        ask = next_analysis(cursor)
        if ask is None:
            break

        start_time = time.time()
        analysis = analysis_api(ask["prompt"])
        response_message = analysis["choices"][0]["message"]

        if response_message.get("function_call"):
            response = response_message["function_call"]["arguments"]
        else:
            response = '{"advice_type": "API_FAILURE"}'

        usage = analysis["usage"]["total_tokens"]
        cursor.execute(
            "update ask set analysis = %s where ask_id = %s",
            (json.dumps(response), ask["ask_id"]),
        )
        conn.commit()
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(
            f"Ask ID: {ask['ask_id']}, Usage: {usage}, Time taken: {elapsed_time} seconds"
        )

    conn.close()
    cursor.close()


def load_random_dicts():
    num_dicts = 100
    with open("db/sample_data.json", "r") as json_file:
        data = json.load(json_file)

    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError("The JSON file should contain a list of dictionaries.")

    random_dicts = random.sample(data, num_dicts)

    conn, cursor = db_connect()
    for idx, dictionary in enumerate(random_dicts, start=1):
        question = dictionary.get("question", "")
        if question:
            ask = new_ask(conn, cursor, question)
            embed_ask(conn, cursor, ask)
            moderate_ask(conn, cursor, ask)
            respond_to_ask(conn, cursor, ask)

            ask_id = ask["ask_id"]
            print(ask_id)


if __name__ == "__main__":
    load_random_dicts()
    # analyze_asks()
    # get_ask("MGlpMj2TunU")

    # load_random_dicts()
    # embed_asks()
# moderate_asks()

# conn, cursor = db_connect()
# ask = random_ask(cursor)
# content = ask["analysis"]["choices"][0]["message"]["content"]
# print(json.dumps(content, indent=5))
