# 3408
import psycopg2
import psycopg2.extensions
from psycopg2.extras import DictCursor

import requests
import openai
import json
import random
from datetime import datetime

from config import OPENAI_API_KEY, POSTGRESQL_KEY


openai.api_key = OPENAI_API_KEY
pg_password = POSTGRESQL_KEY


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
        # host="bot-e.cluster-chki9sxssda8.us-east-2.rds.amazonaws.com",
        # user="postgres",
        # password=f"{pg_password}",
        port="5432",
    )
    cursor = conn.cursor(cursor_factory=DictCursor)
    return conn, cursor


def new_question(conn, cursor, question):
    question = question.strip()
    if len(question) < 1:
        return {}
    # insert a new question record and get back the question_id
    cursor.execute("SELECT * FROM new_question(%s)", (question,))
    conn.commit()
    result_tuple = cursor.fetchone()

    column_names = [desc[0] for desc in cursor.description]
    result_dict = dict(zip(column_names, result_tuple))

    return result_dict


def next_embedding(cursor):
    # this returns an question record that is in need of embedding
    cursor.execute("SELECT * FROM next_embedding()")
    return cursor.fetchone()


def next_moderation(cursor):
    # this returns an question record that is in need of moderation
    cursor.execute("SELECT * FROM next_moderation()")
    return cursor.fetchone()


def answer_next(cursor):
    # this returns an question record that is in need of moderation
    cursor.execute(
        """
  SELECT *
  FROM question
  WHERE answer IS NULL
  ORDER BY added_at ASC
  LIMIT 1;
"""
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
                    question_id = notify.payload
                    print(f"recieved notification for new_question: {question_id}")
                    question = answer_next(cursor)
                    break
        else:
            respond_to_question(conn, cursor, question)
            question = answer_next(cursor)


def random_question(cursor):
    # this returns an question record that is in need of analysis
    cursor.execute("SELECT * FROM question order by RANDOM() limit 1")
    return cursor.fetchone()


def get_similar(cursor, question_id):
    # insert a new question record and get back the question_id

    cursor.execute("select question, answer from get_similar(%s)", (question_id,))
    return cursor.fetchone()


def post_question(question):
    conn, cursor = db_connect()
    question = new_question(conn, cursor, question)
    embed_question(conn, cursor, question)
    moderate_question(conn, cursor, question)

    cursor.close()
    conn.close()
    return question


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


def get_questions(question_ids):
    conn, cursor = db_connect()

    # Filter out invalid question_ids
    valid_question_ids = [
        question_id for question_id in question_ids if validate_key(question_id)
    ]

    cursor.execute(
        "select * from question where question_id = ANY(%s)",
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


def similar(question_id):
    conn, cursor = db_connect()

    # Filter out invalid question_ids
    if not validate_key(question_id):
        return "[]"

    cursor.execute(
        "select * from similar(%s)",
        (question_id,),
    )
    questions = cursor.fetchall()
    # Convert the rows to a list of dictionaries
    columns = [desc[0] for desc in cursor.description]
    data = [dict(zip(columns, row)) for row in questions]

    cursor.close()
    conn.close()

    # Convert the list of dictionaries to JSON
    json_response = json.dumps(data, default=custom_json_serializer)
    return json_response


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


def content_compliance(question):
    return question


def advise(question):
    return question


def respond_to_question(conn, cursor, data):
    user_message = data["question"]
    # start_time = time.time()
    with open("data/prompt_bot-e_main.txt", "r") as file:
        system_prompt = file.read()

    question_id = data["question_id"]

    # similar = get_similar(cursor, question_id)
    # similar_answer = similar["answer"]
    # similar_question = similar["question"]
    system_message = (
        # f"{system_prompt}\nquestion:\n{similar_question}\nanswer:\n{similar_answer}"
        f"{system_prompt}"
    )

    completion = openai.ChatCompletion.create(
        # model="gpt-4",
        model="gpt-3.5-turbo",
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
    lines = response_message.split("\n", 1)
    title_line = lines[0]
    rest_of_answer = lines[1]

    title = title_line.split(":", 1)[1].strip()
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
    return get_question(question_id)


def load_random_dicts():
    with open("data/training_data.json", "r") as json_file:
        data = json.load(json_file)

    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError("The JSON file should contain a list of dictionaries.")

    random_dicts = random.sample(data, len(data))  # shuffling the data

    # conn, cursor = db_connect()
    for idx, dictionary in enumerate(random_dicts, start=1):
        question = dictionary.get("question", "")
        if question:
            question_data = {"question": question}
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                "http://localhost:6464/question",
                data=json.dumps(question_data),
                headers=headers,
            )
            if response.status_code == 200:
                data = response.json()
                print(f"new question: {data[0]}")
            else:
                print(response.status_code)


def save_pair(conn, cursor, question, answer):
    cursor.execute(
        "INSERT INTO training_data(question, answer) VALUES(%s, %s)",
        (question, answer),
    )
    conn.commit()


def next_training(cursor):
    # this returns an question record that is in need of embedding
    cursor.execute(
        "SELECT * FROM training_data WHERE question_embedding IS NULL LIMIT 1"
    )
    return cursor.fetchone()


def embed_training():
    conn, cursor = db_connect()
    while True:
        training = next_training(cursor)
        if training is None:
            break

        embedding = embedding_api(training["question"])
        cursor.execute(
            "UPDATE training_data SET question_embedding = %s WHERE training_data_id = %s",
            (embedding, training["training_data_id"]),
        )
        conn.commit()
        print("saved embeddings for: ", training["training_data_id"])
        # time.sleep(0.8)
    conn.close()
    cursor.close()


def process_sample_data():
    file_path = "data/sample_data/consolidated.json"
    conn, cursor = db_connect()
    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
            for item in data:
                if "question" in item and "answer" in item:
                    question = item["question"]
                    answer = item["answer"]
                    save_pair(conn, cursor, question, answer)
                else:
                    print("Invalid data format in JSON item:", item)
    except FileNotFoundError:
        print("File not found:", file_path)
    except json.JSONDecodeError:
        print("Error decoding JSON in the file:", file_path)
    finally:
        conn.close()
        cursor.close()


def export_divergent_records():
    conn, cursor = db_connect()

    # First, get a random record's question_embedding as the reference
    cursor.execute(
        "SELECT question_embedding FROM training_data ORDER BY RANDOM() LIMIT 1;"
    )
    reference_embedding = cursor.fetchone()[0]

    # Then, fetch the 50 most divergent records from the reference embedding
    query = """
    SELECT training_data_id, question, answer
    FROM training_data
    ORDER BY training_data.question_embedding <-> %s DESC
    LIMIT 50;
    """
    cursor.execute(query, (reference_embedding,))
    results = cursor.fetchall()

    # Convert the results to a list of dictionaries
    records = [
        {"training_data_id": r[0], "question": r[1], "answer": r[2]} for r in results
    ]

    # Export the records to a pretty-printed JSON file
    with open("divergent_records.json", "w") as f:
        json.dump(records, f, ensure_ascii=False, indent=4)

    # Close the database connection
    cursor.close()
    conn.close()


# Call the function
# export_divergent_records()


if __name__ == "__main__":
    respond()
    # conn, cursor = db_connect()
    # question = get_question("KiV4OnQED4V", return_json=False)
    # response = respond_to_question(conn, cursor, question)
