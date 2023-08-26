import json
import os


def process_qa_entries(json_list):
    qa_pairs = []
    current_question = []
    current_answer = []
    in_question = True
    question_no = 0

    for index, item in enumerate(json_list):
        if item.startswith("DEAR"):
            if item.startswith("DEAR ABBY:"):
                # If we have a previous question, add it to the list
                if current_question or current_answer:
                    qa_pairs.append(
                        {
                            "question": " ".join(current_question),
                            "answer": " ".join(current_answer),
                        }
                    )
                    current_question = []
                    current_answer = []

                question_no += 1
                current_question.append(item)
                in_question = True
            else:
                current_answer.append(item)
                in_question = False
        else:
            if in_question:
                current_question.append(item)
            else:
                current_answer.append(item)

    # Add the last question-answer pair if it hasn't been added
    if current_question or current_answer:
        qa_pairs.append(
            {"question": " ".join(current_question), "answer": " ".join(current_answer)}
        )

    return qa_pairs


compiled_data = []

# Path to your sub-directory containing the JSON files
sub_directory = "json"

# Loop through all files in the sub-directory
for filename in os.listdir(sub_directory):
    if filename.endswith(".json"):
        with open(os.path.join(sub_directory, filename), "r") as file:
            json_content = json.load(file)
            compiled_data.extend(process_qa_entries(json_content))

# Save the compiled data to a new JSON file
with open("dear_abby.json", "w") as outfile:
    json.dump(compiled_data, outfile, indent=4)

print("Data saved!")
