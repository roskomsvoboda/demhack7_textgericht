import os
import argparse


import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

TYPE_PROMPT = "Определи, является ли текст: новостью, статьёй, записью в личном блоге, публичным комментарием или личным сообщением. Верни только категорию текста. Если текст не относится ни одной из этих категорий, верни 'другое'."

SYSTEM_CONTENT = "Ты - журналист и исследователь российских СМИ, работающий в условиях диктатуры и военной цензуры (война между Россией и Украиной, с вмешательством Европы и США)."
REFERENCES_PROMPT = """Есть ли в тексте ссылки на источники информации? Если они отсутствуют, верни только "Источники: не обнаружены."

Текст:
"""
HATESPEECH_PROMPT = """Проверь текст на наличие дискриминирующих, стигматизирующих или провоцирующих ненависть лексики, высказываний или идей (например, трансфобию, гомофобию, национализм, расизм или сексизм).

Текст:
"""

MANIPULATION_PROMPT = """Извлеки все приёмы манипуляции читателем из следующего текста и их краткое обоснование в виде пронумерованного списка. Если в тексте нет приёмов манипуляции, верни "Манипуляция: не обнаружена".

Текст:
"""

LOGIC_ERR_PROMPT = """Проверь текст (внутри тройной `) на наличие логических ошибок или когнитивных искажений. Если они не обнаружены в тексте, напиши, что "Логические ошибки: не обнаружены". Если они, то сформулируй свой ответ так:
1) Наличие логических ошибок: поочередно перечисли название логических ошибок и для каждой из них кратко (одно предложение) объясни на примере текста, почему это логическая ошибка.
2) Поправка: кратко (в двух предложениях) объясни, почему обнаруженные логические ошибки опасны, и как их избежать.

Например:

Наличие логических ошибок:
1) Атака личности. Уоррен атакует личность Уилла, обвиняя его в ненависти к стране, вместо того чтобы обсуждать его аргументы по поводу военных расходов.
2) Подмена тезиса: Уоррен искажает слова Уилла и потом опровергает своё искажение.

Поправка: Обнаруженные логические ошибки опасны, так как отвлекают от рассмотрения фактов и аргументов, и могут вести к искаженному восприятию ситуации. Чтобы избежать их, важно сосредотачиваться на деле и обсуждении аргументов, а не переходить на личности собеседников.
"""


def process_text(text):
    run_analysis = False
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"{TYPE_PROMPT} Текст: '{text}'"}],
        temperature=0,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
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
        "manipulation_methods": MANIPULATION_PROMPT,
        "hatespeech": HATESPEECH_PROMPT,
        "references": REFERENCES_PROMPT,
    }
    criteria = {field: None for field in field2prompt.keys()}
    for field_name, prompt in field2prompt.items():
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_CONTENT},
                {"role": "user", "content": f"{prompt} '{text}'"},
            ],
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
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
    return criteria


def main(text):
    process_text(text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ChatGPT prompts for the given text.")
    parser.add_argument("text", type=str, help="Input text to be processed.")

    args = parser.parse_args()
    main(args.text)
