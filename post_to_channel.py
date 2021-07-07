import os
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient, connection
import logging
from telethon import sync, TelegramClient, events
from telethon.tl.functions.messages import GetDialogsRequest, GetHistoryRequest
import json
from datetime import datetime, timedelta
import pprint
import pymysql
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session
from telethon.tl.types import MessageEntityTextUrl
from tables.channel_posts import ChannelPost

logging.basicConfig(level=logging.WARNING)
load_dotenv()

engine = create_engine('mysql+pymysql://'+os.getenv('DB_USERNAME')+':'+urllib.parse.quote(os.getenv('DB_PASS'))+'@'+os.getenv('DB_URL')+':'+os.getenv('DB_PORT')+'/'+os.getenv('DB_SCHEMA')+'')
db_conn = engine.connect()
session = Session(engine, future=True)

def post_group():
    try:
        data = session.query(ChannelPost).where(ChannelPost.is_posted == False).order_by(ChannelPost.posted_date).first()
        if data is not None:
            if data.url is not None and data.url != '':
                message = data.message.replace('link', '<a href="' + data.url + '">link</a>')
                # print(message)
                send_message(os.getenv('TL_READ_API_PHONE'), os.getenv('TL_READ_API_ID'), os.getenv('TL_READ_API_HASH'), message)
                data.is_posted = True
                session.commit()
            else:
                message = data.message
                # print(message)
                send_message(os.getenv('TL_READ_API_PHONE'), os.getenv('TL_READ_API_ID'), os.getenv('TL_READ_API_HASH'), message)
                data.is_posted = True
                session.commit()
    except Exception as e:
        print(str(datetime.now()) + " Error other")
        print(e)

def send_message(phone, api_id, api_hash, message):
    folder_session = str(Path(__file__).parent.absolute()) + str('/session/')
    client = TelegramClient(folder_session + phone, api_id, api_hash)
    client.connect()
    if not client.is_user_authorized():
        print(str(datetime.now()) + ' Post to Channel Login fail, need to run init_session')
    else:
        destination_channel_username = os.getenv('POST_TO_USERNAME')
        entity = client.get_entity(destination_channel_username)
        client.send_message(
            entity=entity,
            message=message,
            link_preview=True,
            parse_mode='html'
        )


if 9 < datetime.now().hour < 22:
    post_group()
