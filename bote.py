# 3408
import psycopg2

# DictCursor returns data as dictionaries instead of tuples
from psycopg2.extras import DictCursor
import os
import openai
import time
import json
import random

openai.api_key = os.getenv("OPENAI_API_KEY")

pg_password = os.getenv("POSTGRESQL_KEY")


def db_connect():
    conn = psycopg2.connect(
        host="botty-dev.cluster-chki9sxssda8.us-east-2.rds.amazonaws.com",
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

    conn.close()
    cursor.close()
    return asks


def get_ask(ask_id):
    # Call get_asks with a list containing a single ask_id
    asks = get_asks([ask_id])

    # If get_asks returned a non-empty list, return the first element
    if asks:
        return asks[0]

    # Otherwise, return None
    return None


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


def analysis_api(user_message):
    with open("db/analysis_functions.json", "r") as file:
        functions = json.load(file)
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        # model="gpt-4",
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
    try:
        for idx, dictionary in enumerate(random_dicts, start=1):
            question = dictionary.get("question", "")
            ask = new_ask(conn, cursor, question)
            ask_id = ask["ask_id"]
            print(ask_id)
    except Exception as e:
        print("An error occurred:", e)
    finally:
        conn.close()
        cursor.close()


if __name__ == "__main__":
    analyze_asks()
    # get_ask("MGlpMj2TunU")

    # load_random_dicts()
    # embed_asks()
# moderate_asks()

# conn, cursor = db_connect()
# ask = random_ask(cursor)
# content = ask["analysis"]["choices"][0]["message"]["content"]
# print(json.dumps(content, indent=5))
