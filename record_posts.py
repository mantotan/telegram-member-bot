import os
import urllib.parse
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

def start(phone, api_id, api_hash):
    folder_session = 'session/'
    client = TelegramClient(folder_session + phone, api_id, api_hash)
    client.connect()
    if not client.is_user_authorized():
        print('Login fail, need to run init_session')
    else:
        get_chat(client)

def get_last_id(channel_username):
    res = session.query(ChannelPost).where(ChannelPost.username == channel_username).order_by(ChannelPost.posted_date.desc()).all()
    if len(res) > 0:
        return res[0].message_id
    else:
        return 0

def get_chat(client):
    channel_usernames = eval(os.getenv('RECORD_FROM'))
    for channel_username in channel_usernames:
        last_id = get_last_id(channel_username)
        channel_entity = client.get_entity(channel_username)
        chats = []
        posts = client(GetHistoryRequest(
            peer=channel_entity,
            limit=10,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=last_id,
            add_offset=0,
            hash=0))
        chats.extend(posts.messages)
        for chat in chats:
            # pprint.pprint(chat.to_dict(), width=400)
            # print(str(chat.message))
            if chat.message is not None:
                if channel_username == 'unfolded':
                    if chat.entities is not None and type(chat.entities[0]) is MessageEntityTextUrl:
                        url = str(chat.entities[0].url)
                        # print(str(chat.entities[0].url))
                        action = insert(ChannelPost).values(
                            username=channel_username,
                            group_type='channel',
                            message_type='Message',
                            posted_date=chat.date,
                            message_id=int(chat.id),
                            message=str(chat.message),
                            is_posted=False,
                            url=url
                        )
                        db_conn.execute(action)
                else:
                    action = insert(ChannelPost).values(
                        username=channel_username,
                        group_type='channel',
                        message_type='Message',
                        posted_date=chat.date,
                        message_id=int(chat.id),
                        message=str(chat.message),
                        is_posted=False
                    )
                    db_conn.execute(action)

start(os.getenv('TL_READ_API_PHONE'), os.getenv('TL_READ_API_ID'), os.getenv('TL_READ_API_HASH'))
