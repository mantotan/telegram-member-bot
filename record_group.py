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
from sqlalchemy.exc import IntegrityError

from tables.recorded_channels import RecordedChannel
from tables.my_bots import MyBot
from tables.channel_hashes import ChannelHash

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
            print('Login fail, need to run init_session')
        else:
            print('Login success ' + str(bot.phone))
        get_client_groups(client, bot)


def get_client_groups(client, bot):
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
                save_group_data(chat, bot)
        except:
            continue


def save_channel_hash(group, bot):
    channel_hash = session.query(ChannelHash).where(ChannelHash.channel_id == group.id).where(ChannelHash.bot_api_id == bot.api_id).first()
    if channel_hash is None:
        try:
            insertHash = insert(ChannelHash).values(
                channel_id=group.id,
                bot_api_id=bot.api_id,
                access_hash=group.access_hash
            )
            db_conn.execute(insertHash)
            session.commit()
        except Exception as e:
            print('save channel hash error')
            print(e)


def save_group_data(group, bot):
    try:
        channel = session.query(RecordedChannel).where(RecordedChannel.channel_id == group.id).first()
        if channel == None:
            insertChannel = insert(RecordedChannel).values(
                channel_id=group.id,
                title=group.title,
                date=group.date,
                version=group.version,
                access_hash=group.access_hash,
                is_megagroup=group.megagroup,
                is_inviting=False
            )
            db_conn.execute(insertChannel)
            session.commit()
    except IntegrityError as e:
        print('save group error duplicate')
    except Exception as e:
        print('save group error')
        print(e)
    save_channel_hash(group, bot)


start()
