from dotenv import load_dotenv
from openai import OpenAI


class ServeAI:
    def __init__(self, base_url="http://127.0.0.1:8000/v1", api_key="not-needed"):
        load_dotenv()
        self.base_url = base_url
        self.client = OpenAI(base_url=self.base_url, api_key=api_key)

    def llm_response(self, messages, model="gemma-3-4b-it-UD-Q8_K_XL.gguf"):
        response = self.client.chat.completions.create(
            model=model, messages=messages, stream=False
        )
        return response.choices[0].message.content


# llama.cpp cmd
# ./llama-server --model gemma-3-4b-it-UD-Q8_K_XL.gguf --mmproj mmproj-BF16.gguf --host 127.0.0.1 --port 8000 -c 8192 -ngl 999
