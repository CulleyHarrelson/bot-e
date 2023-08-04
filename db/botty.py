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


def test_db():
    cursor = db_connect()
    cursor.execute(
        "SELECT count(*) FROM get_proximal_ask(ARRAY['test'], ARRAY['test'])"
    )
    advice = cursor.fetchall()
    print(advice)
    cursor.close()


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
    # this returns an ask record that is in need of embedding
    cursor.execute("SELECT * FROM next_moderation()")
    return cursor.fetchone()


def new_ask(conn, cursor, prompt):
    # this returns an ask record that is in need of embedding
    cursor.execute("SELECT * FROM new_ask(%s)", (prompt,))
    conn.commit()
    return cursor.fetchone()


def moderation_api(input_text):
    response = openai.Moderation.create(input=input_text)
    return response


# return response["results"][0]


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


def load_random_dicts():
    num_dicts = 50
    with open("sample_data.json", "r") as json_file:
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
    # load_random_dicts()
    # embed_asks()
    #moderate_asks()

    # for idx, dictionary in enumerate(random_dicts, start=1):
    #    print(f"Random Dictionary {idx}:")
    #    print(dictionary)
    #    print()
