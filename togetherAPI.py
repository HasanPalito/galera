
import requests
def querry_translate(queery):
    headers = {
    'Authorization': 'Bearer ' + "",
    'Content-Type': 'application/json',
    }
    content = 'from this string: "REPLACE" \nobject = be specific, what object is in sentence, analyze objective characteristic of the object like color,shape and etc , if there is no object return "NONE".\nperson = is there a persons name in the sentence, give me his/her name with objective characteristic if any .\nactivity =  from the sentence what are people doing if nothing found return "NONE"\nplace = from the sentence where is the place.\ntime =based on the sentence when is the time if nothing found return "NONE"\ndescription = decsribe the image as objectively as possible do not include subjectivity.\n\nONLY RESPONSE AS JSON, DO NOT ADD ANYTHING ELSE LIKE "Here is the JSON response:"\nUsing this JSON schema:\n        response = {"object": str, "person":str,place":str,"activity":str"time":str}'
    res=content.replace("REPLACE",queery)
    json_data = {
        'model': 'meta-llama/Llama-3-8b-chat-hf',
        'messages': [
            {
                'role': 'user',
                'content': res,
            },
        ],
        'max_tokens': 50,
        'temperature': 0.7,
        'top_p': 0.7,
        'top_k': 50,
        'repetition_penalty': 1,
        'stop': '["<|eot_id|>"]',
        'stream': False,
    }

    response = requests.post('https://api.together.xyz/v1/chat/completions', headers=headers, json=json_data)
    a=response.json()
    return a["choices"][0]["message"]["content"]
