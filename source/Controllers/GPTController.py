import os

import openai


def analyze_text(text: str, prompts: dict):
    field2prompt = {
        "manipulation_methods": prompts['manipulation_prompt'],
        "hatespeech": prompts['hatespeech_prompt'],
        "references": prompts['references_prompt'],
        "logical_fallacies": prompts['logical_fallacy_prompt'],
    }
    criteria = {field: None for field in field2prompt.keys()}
    for field_name, prompt in field2prompt.items():
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Assistant is a large language model trained by OpenAI"},
                {"role": "user", "content": f"{prompt} '{text}'"},
            ],
        )
        answer = response["choices"][0]["message"]["content"]
        criteria[field_name] = answer
    if criteria["references"] == "Источники: не обнаружены.":
        criteria["references_present"] = 0
    else:
        criteria["references_present"] = 1
    if "Манипуляция: не обнаружена" in criteria["manipulation_methods"]:
        criteria["manipulation_present"] = 0
    else:
        criteria["manipulation_present"] = 1
    if "Логические ошибки: не обнаружены" in criteria["logical_fallacies"]:
        criteria["logical_fallacies_present"] = 0
    else:
        criteria["logical_fallacies_present"] = 1
    return criteria

class GPTController:
    def __init__(self, api_key):
        openai.api_key = api_key
    def process_text(text: str, prompts_dir: str):
        prompts = {}
        for f in os.listdir(prompts_dir):
            if f.endswith('_prompt.txt'):
                with open(os.path.join(prompts_dir, f), 'r', encoding='utf-8') as f_in:
                    prompts[f.replace('.txt', '')] = '\n'.join(f_in.readlines())
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"{prompts['type_prompt']} '{text}'"}],
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        text_type = response["choices"][0]["message"]["content"]
        if text_type.lower() != "личное сообщение":
            return analyze_text(text, prompts)
        else:
            return ("Этот текст похож на личное сообщение и не будет проверен на наличие манипуляций, "
                    "логических ошибок или hatespeech.")
        