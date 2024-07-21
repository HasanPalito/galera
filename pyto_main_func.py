import firebase_admin
from firebase_admin import credentials,db,initialize_app,storage
import io
from PIL import Image
import face_recognition
import datetime
import numpy as np
import cv2
import requests
import pathlib
from fastapi import FastAPI,UploadFile
from statistics import mode
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
import uvicorn
import json 
import mysql.connector
from datetime import datetime, timezone
import ollama
import numpy as np 
import ntpath
from PIL import Image
import chromadb
import uuid
import os

def init_new_user(username):
     os.mkdir(rf'D:\PYTO\{username}')
     os.mkdir(rf'D:\PYTO\{username}\face_encodings')
     os.mkdir(rf'D:\PYTO\{username}\gallery')
     os.mkdir(rf'D:\PYTO\{username}\gallery\compressed_image')
     os.mkdir(rf'D:\PYTO\{username}\gallery\raw_image')
     os.mkdir(rf'D:\PYTO\{username}\gallery\processed_image')
     f = open(fr'D:\PYTO\{username}/name_encoding_pair.json',"w+")
     f.write("{}")

########################################################################
# REMEMBER THAT IN JSON IT WAS STORE AS LIST WHILE ENCODING IS NPARRAY #
########################################################################

def add_encoding(image_path,username,name):
     image = face_recognition.load_image_file(image_path)
     face_encoding = face_recognition.face_encodings(image)[0]
     
     fp = open(fr'{username}/name_encoding_pair.json')
     data= json.load(fp)
     data[name]= list(face_encoding)
     
     with open(fr'{username}/name_encoding_pair.json', 'w') as json_file:
            json.dump(data, json_file, 
                        indent=4,  
                        separators=(',',': '))
     return 

def return_face_encoding(username):
     f = open(fr'{username}/name_encoding_pair.json')
     data = json.load(f)
     f.close()
     known_face_encodings = []
     known_face_names = []
     for name in data:
          known_face_encodings.append(np.array(data[name]))
          known_face_names.append(name)
     return known_face_encodings, known_face_names

########################################################################
# REMEMBER THAT IN JSON IT WAS STORE AS LIST WHILE ENCODING IS NPARRAY #
########################################################################

def path_leaf(path):
    ntpath.basename("a/b/c")
    try:
     head, tail = ntpath.split(path)
     return tail or ntpath.basename(head)
    except:
         ntpath.basename("a\b\c")
         head, tail = ntpath.split(path)
         return tail or ntpath.basename(head)
         
def compressed(image_path,username):
     filename=path_leaf(image_path)
     foo = Image.open(image_path)
     foo.thumbnail((200,200),Image.LANCZOS)
     foo.save(rf'D:\PYTO\{username}\gallery\compressed_image\{filename}',"JPEG")

def compare(known_face_encodings,face_list,image_path,username):
    face_names = []
    image=cv2.imread(image_path, cv2.IMREAD_COLOR)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            ############ FACE EVAL###################
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = face_list[best_match_index]
            else :
                 name="unknown"
            face_names.append(name)

            ########### EVALUATION DONE#################

    for (top, right, bottom, left), name in zip(face_locations, face_names):
        cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), 2)
        # Draw a label with a name below the face
        bar=22
        size_factor = 0.8
        print(right-left)
        if right - left <200 :
             size_factor= 0.6
        if right - left < 100 :
             size_factor= 0.4
        print(size_factor)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(image, f'name : {name}', (left, bottom+10), cv2.FONT_HERSHEY_SIMPLEX, size_factor, (36,255,12), 2)

    filename= path_leaf(image_path)
    print(filename)
    compressed(image_path,username)
    cv2.imwrite(rf"D:\PYTO\{username}\gallery\processed_image\{filename}",image)
    print (face_names)
    return face_names

chroma_client = chromadb.HttpClient(host='localhost', port=7000)

def upload_path(path,username):
    bucket = storage.bucket()
    timestamp= datetime.now(timezone.utc)
   
    blob = bucket.blob(rf"{username}/{uuid.uuid4()}")
    blob.upload_from_filename(path)
    blob.make_public()
    print(f'Public URL: {blob.public_url}')
    return blob.public_url

def retrieve_audio(username,file_name):
    bucket = storage.bucket()
    blob = bucket.blob(rf"aibeecara/{username}/{file_name}")
    blob.make_public()
    url = blob.public_url
    return url

def create_user_colection_by_name(name):
    collection = chroma_client.create_collection(name=f"{name}")

def find_collection(name):
    collection = chroma_client.get_collection(name= f"{name}")
    return collection

#adding history to user collection
def add_collection_tags(response,username,filename):
     coll=find_collection(username)
     coll.add(
     documents=response,
     ids=f"{filename}"
     )
     return  {"status": "success"}

#function to retrieve history     
def get_coll_related_to_input(username, input,n):
     #searching collection
     coll = find_collection(username)
     #retrieving history
     return coll.query(query_texts= input,n_results= n)

def user_usage(username):
     size = 0
     # assign folder path
     Folderpath = rf'D:\PYTO\{username}'
     # get size
     for path, dirs, files in os.walk(Folderpath):
          for f in files:
               fp = os.path.join(path, f)
               size += os.path.getsize(fp)
     return size


cred = credentials.Certificate('audioplayer-b671b-firebase-adminsdk-zr8go-d282e542ee.json')
initialize_app(cred,{
    'storageBucket': 'audioplayer-b671b.appspot.com'
})
