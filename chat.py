from openai import OpenAI
import config
import base64


client = OpenAI(
    api_key=config.ZHIPU_API_KEY,
    base_url=config.ZHIPU_BASE_URL,
)


GLM4_FLASH = "glm-4-flash"


SYSTEM_PROMPT = {
    "role": "system",
    "content": "",
}


def chat_with_llm(message, history):
    """与大语言模型对话"""
    messages = [SYSTEM_PROMPT]
    for human, assistant in history:
        messages.append({"role": "user", "content": human})
        messages.append({"role": "assistant", "content": assistant})
    messages.append({"role": "user", "content": message})

    completion = client.chat.completions.create(
        model=GLM4_FLASH,
        messages=messages,
        temperature=0.3,
        stream=True,
    )

    history = history + [(message, "")]
    response = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            response += chunk.choices[0].delta.content
            history[-1] = (message, response)
            yield history
