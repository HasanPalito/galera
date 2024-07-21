import pyto_main_func
import fastapi
from fastapi import UploadFile,File, Form
from typing import Annotated
import os
import google.generativeai as genai
import json
import pathlib
import uvicorn
import uuid
import togetherAPI

app= fastapi.FastAPI()

model = genai.GenerativeModel('gemini-1.5-flash',generation_config={"response_mime_type": "application/json"})
genai.configure(api_key="AIzaSyAPCgcukqHB711N2ViyTtP6JgpIgZLxWr0")

def AI_description(image_path):
    cookie_picture = {
    'mime_type': 'image/png',
    'data': pathlib.Path(image_path).read_bytes()
    }
    prompt = """
        object = be specific, what object is in the picture, give objective characteristic of the object like color,shape and etc (you are free to determine the characacteristic).
        person = who is in the picture, give me his name which is written near his face with the color of green and pair it with objective characteristic of the person like outfit,expression and etc (you are free to determine the characacteristic).
        activity = what are people doing in the picture if you detect person in the picture, if not return 'NONE'
        place = where is the photo taken, only gave the information like cafe restaurant or beach (you are free to determine the place).
        time = when is the photo taken,  only gave the general information morning, night, afternoon, midningt, evaluate this by observing the sky. if there is no sighting of sky return 'NONE'
        description = decsribe the image as objectively as possible do not include subjectivity.
        Using this JSON schema:
        response = {"object": str, "person":str,place":str,"time":str,"description":str}

        Return a `response`
        """

    response = model.generate_content(
        contents=[prompt, cookie_picture]
        )
    print(response.text)
    return response.text


@app.post("/uploadfile")
async def upload (username:  Annotated[str, Form()],file : Annotated[UploadFile, File()]):
    save_path =os.path.join(rf'D:\PYTO\{username}\gallery\raw_image',file.filename)
    processed_path=os.path.join(rf'D:\PYTO\{username}\gallery\processed_image',file.filename)
    if file.size> 15000000:
        return {"message":"size limit reached"}
    elif file.size> 1000000:
        try:
            with open(save_path, 'wb') as f:
                while contents := file.file.read(1024 * 1024):
                    f.write(contents)
        except Exception:
            return {"message": "There was an error uploading the file"}
        finally:
            file.file.close()
    else :
        try:
            with open(save_path, 'wb') as f:
                while contents := file.file.read():
                    f.write(contents)
        except Exception:
            return {"message": "There was an error uploading the file"}
        
    user_face_encodings, user_face_list = pyto_main_func.return_face_encoding(username)
    if user_face_list != None:
        pyto_main_func.compare(user_face_encodings, user_face_list,save_path,username)
        resp=AI_description(processed_path)
    else :
        resp=AI_description(save_path)
    pyto_main_func.add_collection_tags(resp,username,file.filename)
    pyto_main_func.compressed(save_path,username)

    return {"message": f"Successfully uploaded {file.filename}"}

@app.post("/create_user/{username}")
async def create_user(username):
    pyto_main_func.init_new_user(username=username)
    pyto_main_func.create_user_colection_by_name(username)
    return {"status":"success"}

@app.post("/uploadfile/addencoding")
async def add_encoding(username:  Annotated[str, Form()],file : Annotated[UploadFile, File()],name:  Annotated[str, Form()]):
    save_path =os.path.join(rf'D:\PYTO\{username}\face_encodings',file.filename)
    if file.size> 15000000:
        return {"message":"size limit reached"}
    elif file.size> 1000000:
        try:
            with open(save_path, 'wb') as f:
                while contents := file.file.read(1024 * 1024):
                    f.write(contents)
        except Exception as e:
            print(e)
            return {"message": "There was an error uploading the file"}
        finally:
            file.file.close()
    else :
        try:
            with open(save_path, 'wb') as f:
                while contents := file.file.read():
                    f.write(contents)
        except Exception as e:
            print(e)
            return {"message": "There was an error uploading the file"}
        
    pyto_main_func.add_encoding(save_path,username,name)   
    return {"message": f"Successfully uploaded {file.filename}, encoding added"}

@app.post("/queeryfile/")
async def retrieveFiles(username:  Annotated[str, Form()],querry:  Annotated[str, Form()],n:  Annotated[int, Form()]):
    translated=togetherAPI.querry_translate(querry)
    strat =translated.find('{')
    end =translated.find('}')
    what=translated[strat:end+1]
    res = json.loads(what)
    res["description"]=querry
    query=json.dumps(res)
    print(translated[strat:end+1])
    print("hello")
    alpha =pyto_main_func.get_coll_related_to_input(username,querry,n)
    url_dict={}
    print(alpha["ids"][0])
    for filename,distance,tags in zip(alpha["ids"][0],alpha["distances"][0],alpha["documents"][0]):
        path = os.path.join(rf'D:\PYTO\{username}\gallery\compressed_image',filename)
        url= pyto_main_func.upload_path(path,username)
        url_dict[filename]={"url":url,"distance":distance,"description":tags}
    return {"result": url_dict}

@app.post("/image/raw")
async def retrieveRawFiles(username:  Annotated[str, Form()],filename:  Annotated[str, Form()]):
    path = os.path.join(rf'D:\PYTO\{username}\gallery\raw_image',filename)
    url= pyto_main_func.upload_path(path,username)
    return {filename:url}

@app.get("/usage/{username}")
async def retrieveRawFiles(username):
    size = pyto_main_func.user_usage(username)
    size_in_mb= size/1000000
    return {"usage": size_in_mb}

      
if __name__ == "__main__":
    #packetriot tunnel is connected to porst 80 -- config it in ur own terminal
    uvicorn.run(app=app,host="0.0.0.0",port=80)

