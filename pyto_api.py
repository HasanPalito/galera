import pyto_main_func
import fastapi
from fastapi import UploadFile,File, Form
from typing import Annotated
import os
import google.generativeai as genai
import json
import pathlib
import uvicorn
import togetherAPI
import encription_function as enc
from mimetypes import guess_extension
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
import requests
from jose import jwt
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
import jwt
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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Replace these with your own values from the Google Developer Console
GOOGLE_CLIENT_ID = "495043862553-0mgs5p9uiutd5e2d6jou1j9553ricr4i.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_REDIRECT_URI = "http://localhost/"

def validate(token):
    try:
        # Validate the JWT token using the same secret used to sign it
        payload = jwt.decode(token, GOOGLE_CLIENT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
@app.get("/login", response_class=RedirectResponse)
async def redirect_fastapi():
    return "https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=495043862553-0mgs5p9uiutd5e2d6jou1j9553ricr4i.apps.googleusercontent.com&redirect_uri=http://localhost/&scope=openid%20profile%20email&access_type=offline"

@app.get("/")
async def auth_google(code: str):
    token_url = "https://accounts.google.com/o/oauth2/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    print(code)
    response = requests.post(token_url, data=data)
    access_token = response.json().get("access_token")
    user_info = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", headers={"Authorization": f"Bearer {access_token}"})
    print(user_info.json())
    jwt_token = jwt.encode({
        "id": user_info.json()["id"],
        "email": user_info.json()["email"],
        "name" : user_info.json()["name"]
    },  GOOGLE_CLIENT_SECRET, algorithm="HS256")

    return {"jwt_token": jwt_token,"user_info":user_info.json()}

@app.get("/ping")
async def get_token(token: str = Depends(oauth2_scheme)):
    print("hello")
    try:
        # Validate the JWT token using the same secret used to sign it
        payload = jwt.decode(token, GOOGLE_CLIENT_SECRET, algorithms=["HS256"])
        return {"message": "Token is valid", "payload": payload}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@app.post("/uploadfile")
async def upload (file : Annotated[UploadFile, File()],user_key:  Annotated[str, Form()],token: str = Depends(oauth2_scheme)):
    payload=validate(token)
    username=payload["id"]
    save_path =os.path.join(rf'{username}\gallery\raw_image',file.filename)
    processed_path=os.path.join(rf'{username}\gallery\processed_image',file.filename)
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
    unlabelled_user_face_encodings, unlabelled_user_face_list = pyto_main_func.return_face_encoding(username,is_known=False)
    if user_face_list != None and unlabelled_user_face_list != None:
        pyto_main_func.compare(user_face_encodings, user_face_list,save_path,username,unlabelled_user_face_encodings,unlabelled_user_face_list,user_key)
        resp=AI_description(processed_path)
        enc.encrypt_file(user_key,processed_path)
    else :
        resp=AI_description(save_path)
        
    pyto_main_func.add_collection_tags(resp,username,file.filename)
    compressed_path=pyto_main_func.compressed(save_path,username)
    enc.encrypt_file(user_key,save_path)
    enc.encrypt_file(user_key,compressed_path)
    return {"message": f"Successfully uploaded {file.filename}"}

@app.post("/create_user/")
async def create_user(token: str = Depends(oauth2_scheme)):
    payload=validate(token)
    username=payload["id"]
    pyto_main_func.init_new_user(username=username)
    pyto_main_func.create_user_colection_by_name(username)
    key=enc.generate_key()
    return {"status":"success", "key":key}

@app.post("/uploadfile/addencoding")
async def add_encoding(file : Annotated[UploadFile, File()],name:  Annotated[str, Form()],user_key:  Annotated[str, Form()],token: str = Depends(oauth2_scheme)):
    payload=validate(token)
    username=payload["id"]
    extension=guess_extension(file.filename)
    dafile_name=f"{name}.{extension}"
    save_path =os.path.join(rf'{username}\face_encodings',dafile_name)
    
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
    enc.encrypt_file(user_key,save_path)
    return {"message": f"Successfully uploaded {file.filename}, encoding added"}

@app.post("/queeryfile/")
async def retrieveFiles(querry:  Annotated[str, Form()],n:  Annotated[int, Form()],user_key:  Annotated[str, Form()],token: str = Depends(oauth2_scheme)):
    payload=validate(token)
    username=payload["id"]
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
        path = os.path.join(rf'{username}\gallery\compressed_image',filename)
        enc.decrypt_file(user_key,path)
        url= pyto_main_func.upload_path(path,username)
        enc.encrypt_file(user_key,path)
        url_dict[filename]={"url":url,"distance":distance,"description":tags}
    return {"result": url_dict}

@app.post("/image/raw")
async def retrieveRawFiles(filename:  Annotated[str, Form()],user_key:  Annotated[str, Form()],token: str = Depends(oauth2_scheme)):
    payload=validate(token)
    username=payload["id"]
    path = os.path.join(rf'{username}\gallery\raw_image',filename)
    enc.decrypt_file(user_key,path)
    url= pyto_main_func.upload_path(path,username)
    enc.encrypt_file(user_key,path)
    return {filename:url}

@app.get("/usage")
async def retrieveRawFiles(token: str = Depends(oauth2_scheme)):
    payload=validate(token)
    username=payload["id"]
    size = pyto_main_func.user_usage(username)
    size_in_mb= size/1000000
    return {"usage": size_in_mb}

@app.post("/image/recognized_faces")
async def retrieve_all_recognized_faces(username:  Annotated[str, Form()],user_key:  Annotated[str, Form()],token: str = Depends(oauth2_scheme)):
    payload=validate(token)
    username=payload["id"]
    return pyto_main_func.return_all_face_inDIR(username,user_key,"face_encodings")

@app.post("/image/unrecognized_faces")
async def retrieve_all_unrecognized_faces(user_key:  Annotated[str, Form()],token: str = Depends(oauth2_scheme)):
    payload=validate(token)
    username=payload["id"]
    return pyto_main_func.return_all_face_inDIR(username,user_key,"unrecognized")
      
@app.post("/image/unrecognized_faces/recognize")
async def recognizes(name:  Annotated[str, Form()],da_unrecognized:  Annotated[str, Form()],token: str = Depends(oauth2_scheme)):
    payload=validate(token)
    username=payload["id"]
    pyto_main_func.recog_from_unrecog(username,name,da_unrecognized)
    return {"status":"success"}

if __name__ == "__main__":
    #packetriot tunnel is connected to porst 80 -- config it in ur own terminal
    uvicorn.run(app=app,host="0.0.0.0",port=80)

