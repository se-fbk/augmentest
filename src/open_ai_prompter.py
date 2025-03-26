import os
from openai import OpenAI
from config import *

class OpenAIPrompter:
    def __init__(self):
        self.client = OpenAI(api_key=openai_api_key,)

    def get_completion(self, user_message):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You will be provided with a Java class details in JSON string, and your task is to write an appropriate assertion for the given test case. No explanation or markdown formatting/tick needed."
                },
                {
                    "role": "user",
                    "content": f'"{user_message}"'
                }
            ],
            temperature=0.7,
            max_tokens=256,
            top_p=1
        )
        # print("Response : ",response.choices[0].message.content)
        # return response.choices[0].message.content
        return response

# Example usage:
# helper = OpenAIChatHelper()
# result = helper.get_completion("Your JSON string here")
# print(result)
