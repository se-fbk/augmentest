# ---------------------------------------------------------------------
# Script: OpenAI RAG Test Oracle Generator
# Developer: Shaker Mahmud Khandaker
# Project: AugmenTest
# Last Updated: 2025-03-20
# Purpose: Generates test assertions using OpenAI's RAG API by
#          querying project-specific vector stores and code context.
# ---------------------------------------------------------------------

import os
import json
from openai import OpenAI
from config import *
from colorama import Fore, Style, init

class OpenAIRagPrompter:
    def __init__(self):
        self.client = OpenAI(api_key=openai_api_key,)
        self.assistant_id = "asst_84zBlpRLN2O5er3gU9y1EleC"

    def get_completion(self, user_message, project_id):
        vector_store_id = self.get_vector_store_id(project_id, vector_store_json)
        # print("VS : " + vector_store_id)
        thread = self.client.beta.threads.create(
            messages=[ { "role": "user", "content": f'"{user_message}"'} ],
            tool_resources={
                "file_search": {
                "vector_store_ids": [vector_store_id]
                }
            }
        )
        
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=self.assistant_id
        )

        messages = list(self.client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

        # print("RESPONSE : " + str(messages))
        if messages and messages[0].content:
            message_content = messages[0].content[0].text
            annotations = message_content.annotations
            citations = []
            for index, annotation in enumerate(annotations):
                message_content.value = message_content.value.replace(annotation.text, "")
                if file_citation := getattr(annotation, "file_citation", None):
                    cited_file = self.client.files.retrieve(file_citation.file_id)
                    citations.append(f"[{index}] {cited_file.filename}")

            # print(message_content.value)
            # print("\n".join(citations))
            
            return messages, message_content.value
        else:
            return "", ""
    
    def get_vector_store_id(self, project_name, json_file_path):
        try:
            # Load the JSON data from the file
            with open(json_file_path, 'r') as file:
                project_vector_ids = json.load(file)
            
            # Retrieve the vector store ID for the given project name
            vector_store_id = project_vector_ids.get(project_name)
            
            if vector_store_id:
                return vector_store_id
            else:
                return f"Vector store ID not found for project: {project_name}"
        
        except FileNotFoundError:
            return f"JSON file not found: {json_file_path}"
        except json.JSONDecodeError:
            return "Error decoding JSON file."

    
# openai_rag = OpenAIRagPrompter()

# # RAG example
# user_message = "A Java project includes a class called `AcceptorModel`.\r\nWe need a test oracle for a JUnit test case based on the information you can find in the provided files and DEVELOPER COMMENTS of the method to test its functionality.\r\nIn the following the test case, replace the `__ASSERTION_PLACEHOLDER__` with an appropriate assertion:\r\n```\r\n@Test(timeout = 4000)\n  public void test1()  throws Throwable  {\n      String string0 = AcceptorModel.fromByte((byte)6);\n      __ASSERTION_PLACEHOLDER__\n  }\n```\r\nJust write the assertion statement for the placeholder, not the whole test. No explanation or markdown formatting\/tick needed."
# project_name = "B_PyramidTechnologies-jPyramid-RS-232.AcceptorModel"
# raw_response, response = openai_rag.get_completion(user_message, project_name)

            
# print("Response: " + Fore.GREEN + response, Style.RESET_ALL)
# print("RAW Response: " + Fore.GREEN + str(raw_response), Style.RESET_ALL)




