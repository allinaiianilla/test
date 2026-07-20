from openai import OpenAI
from config import *
client=OpenAI(api_key=API_KEY,base_url=BASE_URL)
def chat(messages):
    try:
        r=client.chat.completions.create(model=MODEL,messages=messages,temperature=TEMPERATURE,stream=True)
        return True,r
    except Exception:
        r=client.chat.completions.create(model=MODEL,messages=messages,temperature=TEMPERATURE)
        return False,r
