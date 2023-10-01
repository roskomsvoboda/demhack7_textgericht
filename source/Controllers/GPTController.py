import openai
import telegram
import asyncio

class GPTController:

    def __init__(self, api_key):
        openai.api_key = api_key
    
    def check_url(self, url, reply_lang="As text"):
        return "Nothing to say for now"

    def check_text(self, message, reply_lang="As text"):
        # Give context to the message
        messages = [
            {"role": "system", 
            "content": "You are ChatGPT, a large language model trained by OpenAI."},  
        ]
        if reply_lang == "As text":
            messages.append(
                {"role": "system", 
                "content": "Answer in a language of the given text"}
            )
        else:
            messages.append(
                {"role": "system", 
                "content": "Answer in {} language as concisely as possible".format(reply_lang) }
            )
        messages.append(
            {"role": "user", "content": message},
        )
        chat = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=messages
            )
        return chat.choices[0].message.content
        