import os
import re
import openai


def analyze_text(text: str, prompts: dict, parse_patterns: list, reply_lang):
    field2prompt = {
        #"manipulation_methods": prompts['manipulation_prompt'],
        #"hatespeech": prompts['hatespeech_prompt'],
        #"references": prompts['references_prompt'],
        "logical_fallacies": prompts['logical_fallacy_prompt'],
        #"references_present": 0,
        #"manipulation_present": 0,
        "logical_fallacies_present": 0
    }
    criteria = {field: None for field in field2prompt.keys()}
    for field_name, prompt in field2prompt.items():
        if not bool(re.match(r'.*_present', field_name)):

            messages=[{"role": "system", "content": "Assistant is a large language model trained by OpenAI"}]
            if reply_lang == "As text":
                messages.append({"role": "system", "content": "Answer in a language of the given text"} )
            else:
                messages.append({"role": "system", "content": "Answer in {} language as concisely as possible".format(reply_lang) })
            messages.append({"role": "user", "content": f"{prompt} '{text}'"})
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )
            answer = response["choices"][0]["message"]["content"].split('\n\n')
            for idx, ans_el in enumerate(answer):
                if sum(bool(pattern.match(ans_el)) for pattern in parse_patterns):
                    #answer[idx] = re.sub(r'\..*', '.', ans_el)
                    criteria[f"{field_name}_present"] = 1
            criteria[field_name] = answer
    return criteria

class GPTController:
    def __init__(self, api_key):
        openai.api_key = api_key
    
    def check_url(self, url, reply_lang="As text"):
        return "Nothing to say for now"

    def process_text(self, text: str, parse_patterns: list, prompts_dir='./prompts/', reply_lang="As text"):
        prompts = {}
        for f in os.listdir(prompts_dir):
            if f.endswith('_fallacy_prompt.txt'):
                with open(os.path.join(prompts_dir, f), 'r', encoding='utf-8') as f_in:
                    prompts[f.replace('.txt', '')] = '\n'.join(f_in.readlines())
        if len(text) > 100:
            return analyze_text(text, prompts, parse_patterns,reply_lang)
        else:
            return "Этот текст похож на личное сообщение и не будет проверен на наличие манипуляций логических ошибок или hatespeech."
        
