import os
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient, connection
import logging
from telethon import sync, TelegramClient, events
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, UserStatusOffline, UserStatusRecently, UserStatusLastMonth, \
    UserStatusLastWeek, Channel, ChatPhoto, ChatPhotoEmpty, UserStatusOnline
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from tables.recorded_channels import RecordedChannel
from tables.telegram_users import TelegramUser

logging.basicConfig(level=logging.WARNING)
load_dotenv()

engine = create_engine('mysql+pymysql://'+os.getenv('DB_USERNAME')+':'+urllib.parse.quote(os.getenv('DB_PASS'))+'@'+os.getenv('DB_URL')+':'+os.getenv('DB_PORT')+'/'+os.getenv('DB_SCHEMA')+'')
db_conn = engine.connect()
session = Session(engine, future=True)


def start(phone, api_id, api_hash):
    folder_session = str(Path(__file__).parent.absolute()) + str('/session/')
    client = TelegramClient(folder_session + phone, api_id, api_hash)
    client.connect()
    if not client.is_user_authorized():
        print('Login fail, need to run init_session')
    else:
        get_client_groups(client, phone)


def get_client_groups(client, phone):
    print('getting data ' + phone)
    chats = []

    query = client(GetDialogsRequest(
        offset_date=None,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=200,
        hash=0
    ))
    chats.extend(query.chats)
    for chat in chats:
        # print(chat)
        try:
            if chat.megagroup is not None and chat.access_hash is not None:
                save_group_data(chat)
        except:
            continue


def save_group_data(group):
    action = insert(RecordedChannel).values(
        channel_id=group.id,
        title=group.title,
        date=group.date,
        version=group.version,
        access_hash=group.access_hash,
        is_megagroup=group.megagroup,
        is_inviting=False
    )
    db_conn.execute(action)

start(os.getenv('TL_GRAB_GROUP_API_PHONE'), os.getenv('TL_GRAB_GROUP_API_ID'), os.getenv('TL_GRAB_GROUP_API_HASH'))
