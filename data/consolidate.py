from simpleaichat import AIChat
from bs4 import BeautifulSoup, NavigableString
from typing import List
import os
import glob
import requests
import re
import pickle
import json


api_key = os.getenv("OPENAI_API_KEY")


def extract_data_from_file(file_path):
    """
    Extracts data from a file specified by the given file_path.

    Args:
        file_path (str): The path to the input file.

    Returns:
        list: A list of dictionaries containing extracted data with keys:
              "question_name", "question", "answer_name", and "answer".
    """
    with open(file_path, "r") as file:
        content = file.read()

    pattern = r"QUESTION(\d+)_NAME\s*:\s*(.*?)\s*QUESTION\1\s*:\s*(.*?)\s*ANSWER\1_NAME\s*:\s*(.*?)\s*ANSWER\1\s*:\s*(.*?)\s*QUESTION\d+"
    matches = re.findall(pattern, content, re.DOTALL)

    pairings = []
    for match in matches:
        question_number, question_name, question, answer_name, answer = match
        pairing = {
            "question_name": question_name.strip(),
            "question": question.strip(),
            "answer_name": answer_name.strip(),
            "answer": answer.strip(),
        }
        pairings.append(pairing)

    return pairings


def process_savage_love_directory():
    """
    Processes the Savage Love directory to extract data from all .txt files
    and saves the extracted data in a JSON file.

    Returns:
        None
    """
    directory_path = "savage_love/results"
    pairings_list = []
    for file_name in os.listdir(directory_path):
        if file_name.endswith(".txt"):
            file_path = os.path.join(directory_path, file_name)
            pairings = extract_data_from_file(file_path)
            pairings_list.extend(pairings)

    output_file = "savage_love/savage_love.json"
    with open(output_file, "w") as json_file:
        json.dump(pairings_list, json_file, indent=2)


def extract_prudence_conversation(json_content):
    """
    Extracts conversations from the given JSON content.

    Args:
        json_content (str or list): The JSON content as a string or list.

    Returns:
        list: A list of extracted conversation texts.
    """
    if isinstance(json_content, str):
        json_content = json.loads(json_content)

    text_values = []
    for item in json_content:
        text = json.loads(item)
        text_values.append(text["text"])
    return text_values


def extract_dear_prudence_conversations():
    """
    Extracts conversations from the Dear Prudence directory and saves the extracted
    data in a JSON file.

    Returns:
        None
    """
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
    with open("dear_prudence/pre_prudence.json", "w") as json_file:
        json.dump(all_conversations, json_file, indent=4)


def find_strong_tag_indices(string_list):
    """
    Finds the indices of strings in the list that start with the "<strong>" tag.

    Args:
        string_list (list): A list of strings.

    Returns:
        list: A list of indices where "<strong>" tagged strings are found.
    """
    # strong_indices = [
    # i for i, string in enumerate(string_list) if string.startswith("<strong>")
    # ]
    strong_indices = []
    pattern = r"^<strong>.*"

    for i, string in enumerate(string_list):
        if re.search(pattern, string):
            if "Good afternoon" in string:
                continue
            strong_indices.append(i)
    return strong_indices


def split_on_strong(string_list):
    """
    Splits the given list of strings based on "<strong>" tagged strings.

    Args:
        string_list (list): A list of strings.

    Returns:
        list: A list of indices where the split occurs.
    """
    strong_indices = find_strong_tag_indices(string_list)

    if len(strong_indices) <= 1:
        return []
    return strong_indices
    return strong_indices


def extract_conversations(string_list, article_id):
    """
    Extracts conversations from the given list of strings based on "<strong>"
    tagged strings, identified using the article_id.

    Args:
        string_list (list): A list of strings.
        article_id (str): The identifier for the article.

    Returns:
        list: A list of dictionaries containing extracted conversations
              with keys "question" and "answer".
    """
    strong_indices = split_on_strong(string_list)

    if len(strong_indices) % 2 != 0:
        print(f"Please investigate the input list for {article_id}")
        return

    conversations = []
    for i in range(0, len(strong_indices), 2):
        question_index = strong_indices[i]
        answer_index = strong_indices[i + 1]

        if i + 2 < len(strong_indices):
            next_question_index = strong_indices[i + 2]
            question = " ".join(string_list[question_index:next_question_index])
        else:
            # If this is the last answer, check if there is any text after it.
            question = " ".join(string_list[question_index:])
            if not question.strip():
                print(
                    "Please investigate the input list. Last entry is an incomplete question."
                )
                return

        answer = " ".join(string_list[answer_index : strong_indices[i + 1] + 1])
        conversations.append({"question": question, "answer": answer})

    return conversations


def extract_qa_pairs(index_list, original_list):
    """
    Extracts question-answer pairs from the original_list based on the given
    list of indices.

    Args:
        index_list (list): A list of indices to identify the question-answer pairs.
        original_list (list): The original list of strings.

    Returns:
        list: A list of dictionaries containing question-answer pairs
              with keys "question" and "answer".
    """
    pairs = []
    num_indices = len(index_list)

    for i in range(0, num_indices, 2):
        question_index = index_list[i]
        if i + 1 < num_indices:
            answer_index = index_list[i + 1]
            question = " ".join(original_list[question_index:answer_index])
            answer = " ".join(original_list[answer_index : index_list[i + 1] + 1])
        else:
            # If this is the last question, check if there is any text after it.
            question = " ".join(original_list[question_index:])
            if not question.strip():
                answer = None
            else:
                answer = " ".join(original_list[question_index + 1 :])

        pairs.append({"question": question, "answer": answer})

    return pairs


def find_pairs(index_list, original_list):
    """
    Finds question-answer pairs based on the given list of indices from the
    original_list.

    Args:
        index_list (list): A list of indices to identify the question-answer pairs.
        original_list (list): The original list of strings.

    Returns:
        list: A list of dictionaries containing question-answer pairs
              with keys "question" and "answer".
    """

    def is_answer(text):
        return text.startswith("<strong>A.")

    def is_question(text):
        return (
            text.startswith("<strong>Q.")
            or text.startswith("<strong>Dear Prudence")
            or "<strong>:</strong>" in text
        )

    pairs = []
    num_indices = len(index_list)
    i = 0

    while i < num_indices:
        question_index = index_list[i]
        if i + 1 < num_indices:
            answer_index = index_list[i + 1]
            question = " ".join(original_list[question_index : answer_index + 1])
            answer = " ".join(original_list[answer_index : index_list[i + 1] + 1])
        else:
            # If this is the last question, check if there is any text after it.
            question = " ".join(original_list[question_index:])
            if not question.strip():
                answer = None
            else:
                answer = " ".join(original_list[question_index + 1 :])

        if is_question(original_list[question_index]):
            if is_question(answer):
                # If the question returns True for is_answer, don't append it to pairs.
                # Instead, append it as a question with None as the answer.
                pairs.append({"question": question, "answer": None})
                pairs.append({"question": answer, "answer": None})
            else:
                pairs.append({"question": question, "answer": answer})

            # Restart processing looking for the answer to the question
            i += 1
        elif is_answer(original_list[question_index]):
            # If the answer returns True for is_question, don't append it to pairs.
            # Instead, append the answer as another question with a null answer.
            pairs.append({"question": None, "answer": question})

        i += 2

    return pairs


def extract_strong_and_remainder(input_string):
    """
    Extracts content and author information from the input_string based on
    "<strong>" tagged content.

    Args:
        input_string (str): The input string.

    Returns:
        tuple: A tuple containing the content_author (str) and the remainder (str)
               of the input_string.
    """
    pattern = (
        r"^<strong>(.*?)</strong>(?:<strong>(.*?)</strong>)?(<strong>:</strong>)?(.*)"
    )
    match = re.match(pattern, input_string)

    if match:
        strong_tag1_content = match.group(1)
        strong_tag2_content = match.group(2)
        remainder = match.group(4)

        content_author = strong_tag1_content

        if strong_tag2_content:
            content_author += strong_tag2_content

        content_author = content_author.rstrip(":")
        return (content_author, remainder)
    else:
        return ("", input_string)


def remove_strong_to_end(input_string):
    """
    Removes the "<strong>" tag and everything after it from the input_string.

    Args:
        input_string (str): The input string.

    Returns:
        str: The processed input string.
    """
    start_index = input_string.find("<strong>")
    if start_index != -1:
        input_string = input_string[:start_index]
    return input_string


def process_list_of_dictionaries(input_list):
    """
    Processes a list of dictionaries containing question-answer pairs and
    extracts question and answer content along with their corresponding names.

    Args:
        input_list (list): A list of dictionaries containing question-answer pairs.

    Returns:
        list: A list of processed dictionaries with keys:
              "question", "answer", "question_name", and "answer_name".
    """
    processed_list = []

    for item in input_list:
        question = item["question"]
        answer = item["answer"]

        try:
            question_name, question = extract_strong_and_remainder(question)
        except Exception as e:
            print(f"Error processing question: {question}")
            continue

        try:
            answer_name, answer = extract_strong_and_remainder(answer)
        except Exception as e:
            print(f"Error processing answer: {answer}")
            continue

        question = remove_strong_to_end(question)
        processed_item = {
            "question": question.strip(),
            "answer": answer.strip(),
            "question_name": question_name.strip(),
            "answer_name": answer_name.strip(),
        }
        processed_list.append(processed_item)

    return processed_list


def extract_prudence_adivce():
    """
    Extracts advice from the Dear Prudence directory and saves the extracted
    data in a JSON file.

    Returns:
        None
    """
    with open("dear_prudence/pre_prudence.json", "r") as json_file:
        prudence = json.load(json_file)
        advisements = []
        for article in prudence:
            conversation = article["conversation"]
            advice = split_on_strong(conversation)
            pairs = find_pairs(advice, conversation)
            advisements.extend(pairs)

        advisements = process_list_of_dictionaries(advisements)
        with open("dear_prudence/prudence.json", "w") as json_file:
            json.dump(advisements, json_file, indent=4)


def consolidate_advice():
    # Read the contents of the first JSON file
    with open("savage_love/savage_love.json", "r") as json_file:
        savage_love = json.load(json_file)

    # Read the contents of the second JSON file
    with open("dear_prudence/prudence.json", "r") as json_file:
        dear_prudence = json.load(json_file)

    consolidated_advice = dear_prudence + savage_love
    # Combine the lists from both JSON files
    # consolidated_advice.extend(savage_love)

    # Write the combined data to a new JSON file
    with open("advice.json", "w") as json_output:
        json.dump(consolidated_advice, json_output, indent=4)
        advice_count = len(dear_prudence)
        print(f"added {advice_count} pieces of advice to advice.json")


if __name__ == "__main__":
    extract_prudence_adivce()
    consolidate_advice()
