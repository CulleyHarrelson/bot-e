from simpleaichat import AIChat
from bs4 import BeautifulSoup, NavigableString
import os
import json
import random


api_key = os.getenv("OPENAI_API_KEY")


def extract_prudence_conversation(json_content):
    if isinstance(json_content, str):
        json_content = json.loads(json_content)

    text_values = []
    for item in json_content:
        text = json.loads(item)
        text_values.append(text["text"])
    return text_values


def extract_dear_prudence_conversations():
    input_directory = "dear_prudence/results"
    all_conversations = []

    for file_name in os.listdir(input_directory):
        if file_name.endswith(".json"):
            file_path = os.path.join(input_directory, file_name)
            with open(file_path, "r") as file:
                content = file.read()
                chat = extract_prudence_conversation(content)

                all_conversations.append(
                    {
                        "article": file_name.rsplit(".", 1)[0],  # Remove the extension
                        "conversation": chat,
                    }
                )

    # return all_conversations
    with open("dear_prudence/prudence.json", "w") as json_file:
        json.dump(all_conversations, json_file, indent=4)


def random_file():
    input_directory = "dear_prudence/results"

    all_files = os.listdir(input_directory)

    # Filter list to only JSON files
    json_files = [file for file in all_files if file.endswith(".json")]

    # Select a random JSON file
    random_file = random.choice(json_files)

    # Return the full path of the selected file
    with open(os.path.join(input_directory, random_file), "r") as file:
        content = file.read()
        chat = extract_prudence_conversation(content)
        for comment in chat:
            print(comment)


if __name__ == "__main__":
    extract_dear_prudence_conversations()
    with open("dear_prudence/prudence.json", "r") as json_file:
        prudence = json.load(json_file)
        print(prudence[0]["conversation"][0])
