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
from datetime import datetime, timezone
import numpy as np 
import ntpath
from PIL import Image
import chromadb
import uuid
import os
import encription_function as enc

def init_new_user(username):
     os.mkdir(rf'{username}')
     os.mkdir(rf'{username}\unrecognized')
     os.mkdir(rf'{username}\face_encodings')
     os.mkdir(rf'{username}\gallery')
     os.mkdir(rf'{username}\gallery\compressed_image')
     os.mkdir(rf'{username}\gallery\raw_image')
     os.mkdir(rf'{username}\gallery\processed_image')
     f = open(fr'{username}/name_encoding_pair.json',"w+")
     f.write("{}")
     f = open(fr'{username}/unrecognized_encoding_pair.json',"w+")
     f.write("{}")

########################################################################
# REMEMBER THAT IN JSON IT WAS STORE AS LIST WHILE ENCODING IS NPARRAY #
########################################################################

def add_encoding(image_path,username,name,is_known=True):
     image = face_recognition.load_image_file(image_path)
     face_encoding = face_recognition.face_encodings(image)[0]
     if is_known:
          path=fr'{username}/name_encoding_pair.json'
     else:
          path=fr'{username}/unrecognized_encoding_pair.json'
     fp = open(path)
     data= json.load(fp)
     data[name]= list(face_encoding)
     
     with open(path, 'w') as json_file:
            json.dump(data, json_file, 
                        indent=4,  
                        separators=(',',': '))
     return 
def add_encoding_from_frame(image,username,name,is_known=True):
     face_encoding = face_recognition.face_encodings(image)[0]
     if is_known:
          path=fr'{username}/name_encoding_pair.json'
     else:
          path=fr'{username}/unrecognized_encoding_pair.json'
     fp = open(path)
     data= json.load(fp)
     data[name]= list(face_encoding)
     
     with open(path, 'w') as json_file:
            json.dump(data, json_file, 
                        indent=4,  
                        separators=(',',': '))
     return 

def return_face_encoding(username,is_known=True):
     if is_known:
          path=fr'{username}/name_encoding_pair.json'
     else:
          path=fr'{username}/unrecognized_encoding_pair.json'
     f = open(path)
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
     save_path=rf'{username}\gallery\compressed_image\{filename}'
     foo.save(save_path,"JPEG")
     return save_path

def compare(known_face_encodings,face_list,image_path,username,unlabelled_known_face_encodings=None,unlabelled_face_list=None,user_key=None):
    face_names = []
    image=cv2.imread(image_path, cv2.IMREAD_COLOR)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)


    for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            ############ FACE EVAL###################
          try:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            print(face_distances)
            if matches[best_match_index]:
                name = face_list[best_match_index]
            else :
                try:
                    unknown_matches = face_recognition.compare_faces(unlabelled_known_face_encodings, face_encoding)
                    unknown_face_distances = face_recognition.face_distance(unlabelled_known_face_encodings, face_encoding)
                    best_match_index = np.argmin(unknown_face_distances)
                    if  unknown_matches[best_match_index]:
                         name = unlabelled_face_list[best_match_index]
                    else :
                         name="unrecognized"
                    face_names.append(name)
                except:
                    name="unrecognized"
            face_names.append(name)
          except:
               name="unrecognized"
               face_names.append(name)
            ########### EVALUATION DONE#################

    for (top, right, bottom, left), name in zip(face_locations, face_names):
        print(left,right,top,bottom)
        # Draw a label with a name below the face
        size_factor = 1.5
        if name == "unrecognized":
             file_path=fr'{username}/unrecognized_encoding_pair.json'
             with open(file_path, 'r') as file:
               data = json.load(file)
             length=len(data)
             img_1=image[top-30:bottom+30,left-30:right+30]
             path=rf'{username}\unrecognized\unrecognized_{length+1}.jpg'
             cv2.imwrite(path, img_1)
             try:
               enc.encrypt_file(user_key,path)
             except:
               print("SUMTING IS WONG")
             add_encoding(path,username,f"unrecognized_{length+1}",False)
             name=f"unrecognized_{length+1}"
        else:
          cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), 2)
          cv2.putText(image, f'name : {name}', (left, bottom+10), cv2.FONT_HERSHEY_SIMPLEX, size_factor, (36,255,12), 2)

    filename= path_leaf(image_path)
    print(filename)
    compressed(image_path,username)
    cv2.imwrite(rf"{username}\gallery\processed_image\{filename}",image)
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
     Folderpath = rf'{username}'
     # get size
     for path, dirs, files in os.walk(Folderpath):
          for f in files:
               fp = os.path.join(path, f)
               size += os.path.getsize(fp)
     return size

def return_all_face_inDIR(username,user_key,DIRNAME):
    user_dir=rf'{username}\{DIRNAME}'
    url_dict={}
    for filename in os.listdir(user_dir):
        file_path = os.path.join(user_dir, filename)
        if os.path.isfile(file_path):
            enc.decrypt_file(file_path,user_key)
            url=upload_path(file_path,username)
            name, extension = os.path.splitext(file_path)
            url_dict[name]=url
            enc.encrypt_file(file_path,user_key)
    return {"url":url_dict}

def recog_from_unrecog(username,name,unrecog):
     recog_path=fr'{username}/name_encoding_pair.json' 
     unrecog_path=fr'{username}/unrecognized_encoding_pair.json'
     recog = open(recog_path)
     unrecog = open(unrecog_path)
     data_unrecog= json.load(unrecog)
     data_recog= json.load(recog)
     data_recog[name]=data_unrecog[unrecog]
     user_dir=rf'{username}\unrecognized'
     for filename in os.listdir(user_dir):
        file_path = os.path.join(user_dir, filename)
        if os.path.isfile(file_path):
            filename, extension = os.path.splitext(file_path)
            if filename==unrecog:
                os.remove(file_path)
     
cred = credentials.Certificate('audioplayer-b671b-firebase-adminsdk-zr8go-d282e542ee.json')
initialize_app(cred,{
    'storageBucket': 'audioplayer-b671b.appspot.com'
})
