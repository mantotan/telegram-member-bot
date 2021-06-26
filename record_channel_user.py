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
        channels = session.query(RecordedChannel).where(RecordedChannel.is_inviting == True).where(RecordedChannel.is_megagroup == True).all()
        for channel in channels:
            get_group_user(client, channel)


def get_existing_user(user_id):
    res = session.query(TelegramUser).where(TelegramUser.user_id == user_id).all()
    if len(res) > 0:
        return res[0]
    else:
        return None


def get_group_user(client, recorded_channel):
    print('Recording Data From ' + str(recorded_channel.title))
    channel = Channel(
        id=recorded_channel.channel_id,
        title=recorded_channel.title,
        date=recorded_channel.date,
        version=recorded_channel.version,
        photo=ChatPhotoEmpty
    )
    all_participants = client.get_participants(channel, aggressive=True)
    print(str(len(all_participants)) + ' entries')
    today = datetime.now()
    last_week = today + timedelta(days=-7)
    last_month = today + timedelta(days=-30)
    for user in all_participants:
        # print(user)
        try:
            last_seen = None
            last_online = None
            if isinstance(user.status, UserStatusRecently):
                last_seen = 'Online'
                last_online = today
            else:
                if isinstance(user.status, UserStatusOnline):
                    last_seen = 'Online'
                    last_online = today
                if isinstance(user.status, UserStatusLastMonth):
                    last_seen = 'Last Month'
                    last_online = last_month
                if isinstance(user.status, UserStatusLastWeek):
                    last_seen = 'Last Week'
                    last_online = last_week
                if isinstance(user.status, UserStatusOffline):
                    last_seen = 'Offline'
                    last_online = user.status.was_online
            existing_user = get_existing_user(user.id)
            if(existing_user is None):
                action = insert(TelegramUser).values(
                    channel_id=channel.id,
                    user_id=user.id,
                    access_hash=user.access_hash,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    has_photo=(user.photo is not None),
                    is_bot=user.bot,
                    last_seen=last_seen,
                    last_online=last_online,
                    is_invited=False
                )
                db_conn.execute(action)
            else:
                existing_user.last_seen = last_seen
                existing_user.last_online = last_online
                session.commit()
        except Exception as e:
            print(user)
            print(e)
            print("Error get user")

start(os.getenv('TL_GRAB_GROUP_API_PHONE'), os.getenv('TL_GRAB_GROUP_API_ID'), os.getenv('TL_GRAB_GROUP_API_HASH'))
