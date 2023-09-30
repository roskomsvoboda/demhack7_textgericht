import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), './prompts/')
PROMPTS = {}
for f in os.listdir(PROMPTS_DIR):
    if f.endswith('_prompt.txt'):
        with open(os.path.join(PROMPTS_DIR, f), 'r', encoding='utf-8') as f_in:
            PROMPTS[f.replace('.txt', '')] = '\n'.join(f_in.readlines())
            

def process_text(text):
    run_analysis = False
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"{PROMPTS['type_prompt']} '{text}'"}]
    )
    text_type = response["choices"][0]["message"]["content"]
    if text_type.lower() != "личное сообщение":
        run_analysis = True
    if run_analysis:
        return analyse_text(text)
    else:
        return {}


def analyse_text(text):
    field2prompt = {
        "manipulation_methods": PROMPTS['manipulation_prompt'],
        "hatespeech": PROMPTS['hatespeech_prompt'],
        "references": PROMPTS['references_prompt'],
        "logical_fallacies": PROMPTS['logical_fallacy_prompt'],
    }
    criteria = {field: None for field in field2prompt.keys()}
    for field_name, prompt in field2prompt.items():
        if 'manipulation' in field_name:
            print(f"{prompt} '{text}'")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": f"{prompt} '{text}'"},
            ]
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
        criteria["manipulation_present"] = 0
    else:
        criteria["manipulation_present"] = 1
    return criteria