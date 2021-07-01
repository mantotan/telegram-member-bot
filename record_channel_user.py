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
from tables.my_bots import MyBot
from tables.user_hashes import UserHash

logging.basicConfig(level=logging.WARNING)
load_dotenv()

engine = create_engine('mysql+pymysql://'+os.getenv('DB_USERNAME')+':'+urllib.parse.quote(os.getenv('DB_PASS'))+'@'+os.getenv('DB_URL')+':'+os.getenv('DB_PORT')+'/'+os.getenv('DB_SCHEMA')+'')
db_conn = engine.connect()
session = Session(engine, future=True)


def start():
    bots = session.query(MyBot).where(MyBot.note == 'invite_user').order_by(MyBot.id).all()

    for bot in bots:
        folder_session = str(Path(__file__).parent.absolute()) + str('/session/')
        client = TelegramClient(folder_session + bot.phone, bot.api_id, bot.api_hash)
        client.connect()
        if not client.is_user_authorized():
            print('Login fail ' + str(bot.phone) + ', need to run init_session')
        else:
            channels = session.query(RecordedChannel).where(RecordedChannel.is_inviting == True).where(RecordedChannel.is_megagroup == True).all()
            for channel in channels:
                get_group_user(client, channel, bot)


def get_existing_user(user_id):
    res = session.query(TelegramUser).where(TelegramUser.user_id == user_id).all()
    if len(res) > 0:
        return res[0]
    else:
        return None


def save_channel_hash(users, bot):
    user_hashes = []
    for idx, user in enumerate(users):
        if user is not None:
            user_hashes.append({
                'user_id': user.id,
                'bot_api_id': bot.api_id,
                'access_hash': user.access_hash
            })
        try:
            if len(user_hashes) >= 1000 or idx == len(users)-1:
                print('insert user hashes ' + str(idx) + ' ' + str(len(user_hashes)))
                db_conn.execute(insert(UserHash).values(user_hashes))
                session.commit()
                user_hashes = []
        except Exception as e:
            print('save channel hash error')
            print(e)

def get_group_user(client, recorded_channel, bot):
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
    telegram_users = []
    for idx, user in enumerate(all_participants):
        # print('append user id ' + str(user.id))
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
            if existing_user is None:
                telegram_users.append({
                    'channel_id': channel.id,
                    'user_id': user.id,
                    'access_hash': user.access_hash,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'has_photo': (user.photo is not None),
                    'is_bot': user.bot,
                    'last_seen': last_seen,
                    'last_online': last_online,
                    'is_invited': False,
                    'invited_date': None
                })

            if len(telegram_users) >= 1000 or idx == len(all_participants)-1:
                if(len(telegram_users) > 0):
                    bulk_insert = insert(TelegramUser).values(telegram_users)
                    db_conn.execute(bulk_insert)
                    session.commit()
                    telegram_users = []
        except Exception as e:
            print(e)
            print("Error get user")
    save_channel_hash(all_participants, bot)

start()
