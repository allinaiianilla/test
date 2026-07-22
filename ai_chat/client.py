from openai import OpenAI
from config import *
import httpx

client=OpenAI(api_key=API_KEY,base_url=BASE_URL,
    http_client=httpx.Client(trust_env=False))
def chat(messages):
    try:
        r=client.chat.completions.create(model=MODEL,messages=messages,temperature=TEMPERATURE,stream=True)
        return True,r
    except Exception:
        r=client.chat.completions.create(model=MODEL,messages=messages,temperature=TEMPERATURE)
        return False,r
