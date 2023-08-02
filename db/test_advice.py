import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
with open("prompt_analysis_prompt.txt", "r") as file:
    content = file.read().lower()

completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "system",
            "content": f"{content}",
        },
        {
            "role": "user",
            "content": "Four years ago, my birth control failed. I never wanted kids and was set to have an abortion, but my husband convinced me it\u2019d be different with our own. It\u2019s not. I\u2019m glad my husband bonded with our daughter, because I wish her no harm but do not love her. My unwillingness to spend time with her made me take on long hours at work, and I am being rewarded with a promotion and raise that requires a transfer to a city 1,000 miles away. I accepted as soon as it was offered. I\u2019m now wondering how to tell my husband that this is a done deal and also that I\u2019d prefer that he and our daughter stay behind. Any thoughts?",
        },
    ],
)

print(completion.choices[0].message)
