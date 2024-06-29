import os

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import json
import re
import traceback
from typing import List

import firebase_admin
import requests
import tensorflow as tf
from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from firebase_admin import credentials, messaging, firestore

from model import message_prediction, url_prediction
from schemas import Messages, SessionName, TokenUpdate, Url

app = FastAPI(debug=True)

cred = credentials.Certificate("./ta-sentinel-fcm-firebase-adminsdk-x3u8h-520cd65cac.json")
print(f"cred: {cred}")
firebase_admin.initialize_app(cred)
db = firestore.client()
device_tokens: List[str] = []

@app.get("/")
def main():
    return 'Hallo'

@app.post("/message-prediction")
def handle_message_prediction(messages: Messages):
    try:
        text_phishing = messages.text
        print(f"text_phishing: {text_phishing}")
        if not text_phishing:
            return JSONResponse(status_code=404, content={"error": "Tidak ada teks yang diberikan"})
        
        results = message_prediction(text_phishing)
        return JSONResponse(status_code=200, content=jsonable_encoder(results))
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "error": str(e)
        })

@app.post("/url-prediction")
def handle_url_prediction(url: Url):
    try:
        url_phishing = url.text
        if not url_phishing:
            return JSONResponse(status_code=404, content={"error": "No url provided"})
        
        results = url_prediction(url_phishing)
        return JSONResponse(status_code=200, content=jsonable_encoder(results))
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "error": str(e)
        })
    
@app.post("/update-token")
async def update_token(token_update: TokenUpdate):
    if not token_update.token:
        raise HTTPException(status_code=400, detail="Token required")
    
    try:
        # Simpan token ke Firestore
        doc_ref = db.collection('token-fcm').document('token-notification')
        doc_ref.set({
            'token': token_update.token
        })
        return {"message": "Token updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update token: {str(e)}")
    
    # # Simpan atau perbarui token di database Anda
    # if token_update.token not in device_tokens:
    #     device_tokens.append(token_update.token)
    # return {"message": "Token updated successfully"}


@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        # print(f"Status message: {data}\n")
        print(json.dumps(data, indent=4))

        if 'payload' in data:
            payload = data['payload']

            if 'from' in payload and 'body' in payload:
                pattern = r'(\d+)@c\.us'
                _id = payload['id']
                # print(f"id: {_id}")
                match = re.search(pattern, _id)
                # print(f"match: {match}")
                sender = match.group(1)
                print(f"sender: {sender}")
                # sender = re.sub(r'')
                sender = re.sub(r'[^0-9]', '', sender)
                print(sender)
                if sender.startswith('62'):
                    sender = '0' + sender[2:]
                message_body = payload['body']
                links = payload['_data']['links']
                nickname = payload['_data']['notifyName']

                print(f"Sender: {sender} \n")
                print(f"Message Body: {message_body} \n")
                print(f"Links: {links} \n")

                result = {
                    "sender": sender,
                    "nickname": nickname
                }

                print('Hallo')

                if message_body and not links:
                    message_payload = Messages(text=[message_body])
                    text_phishing = message_payload.text
                    prediction_result = message_prediction(text_phishing)
                    result['message'] = {
                        "message_body": message_body,
                        "message_prediction": prediction_result
                    }


                    if prediction_result[0]['is_smishing']: #JGN LUPA HAPUS NOTNYA KALO MAU DEPLOY
                        print('MASUKK')
                        print(device_tokens)
                        await send_notification(sender, nickname, message_body)

                # elif not message_body and links:
                #     url_payload = Url(text=[links])
                #     url_phishing = url_payload.text
                #     prediction_result = url_prediction(url_phishing)
                #     result['url'] = {
                #         "url_body": links,
                #         "url_prediction": prediction_result
                #     }

                #     if not prediction_result[0]['is_phishing']:
                #         await send_notification(sender, nickname, links)

                else:
                    message_payload = Messages(text=[message_body])
                    text_phishing = message_payload.text
                    message_prediction_result = message_prediction(text_phishing)

                    urls = [link['link'] for link in links]
                    url_payload = Url(text=urls)
                    url_phishing = url_payload.text
                    url_prediction_result = url_prediction(url_phishing)
                    
                    result['message'] = {
                        "message_body": message_body,
                        "message_prediction": message_prediction_result
                    }
                    result['url'] = {
                        "url_body": links,
                        "url_prediction": url_prediction_result
                    }

                    if message_prediction_result[0]['is_smishing'] or url_prediction_result[0]['is_phishing']:
                        await send_notification(sender, nickname, message_body)

                print(result) 
                return JSONResponse(status_code=200, content=jsonable_encoder(result))
            else:
                return JSONResponse(status_code=404, content={
                    "error": "'from' or 'body' key not found in payload"
                })
        else:
            return JSONResponse(status_code=404, content={
                "error": "'payload' key not found in data"
            })
    except Exception as e:
        traceback.print_exc()  # This will print the traceback to the console
        return JSONResponse(status_code=500, content={
            "error": str(e)
        })
    
async def send_notification(sender, nickname, message):
    try:
        # Ambil token dari Firestore
        doc_ref = db.collection('token-fcm').document('token-notification')
        doc = doc_ref.get()
        if doc.exists:
            token = doc.to_dict().get('token')
            print(f"Token: {token}")
            
            if token:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=f'🚨 Phishing dari {sender} ({nickname})',
                        body=f"{message}"
                    ),
                    token=token,
                    android=messaging.AndroidConfig(
                        priority='high',
                    ),
                    apns=messaging.APNSConfig(
                        headers={'apns-priority': '10'},
                    ),
                )

                # Kirim notifikasi
                response = messaging.send(message)
                print('Successfully sent message:', response)
            else:
                print('No token found in Firestore')
        else:
            print('Document does not exist in Firestore')
    except Exception as e:
        print(f"Error sending notification: {str(e)}")