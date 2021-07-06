import os
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
import logging
from telethon import sync, TelegramClient, events
from telethon.tl.types import InputPeerChannel
from telethon.tl.types import InputPeerUser
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, FloodWaitError
import time
import traceback
import datetime
import os
import json
from sys import exit
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from tables.telegram_users import TelegramUser
from tables.my_bots import MyBot
from tables.channel_hashes import ChannelHash
from tables.user_hashes import UserHash

load_dotenv()

engine = create_engine('mysql+pymysql://'+os.getenv('DB_USERNAME')+':'+urllib.parse.quote(os.getenv('DB_PASS'))+'@'+os.getenv('DB_URL')+':'+os.getenv('DB_PORT')+'/'+os.getenv('DB_SCHEMA')+'')
db_conn = engine.connect()
session = Session(engine, future=True)

folder_session = str(Path(__file__).parent.absolute()) + str('/session/')
logging.basicConfig(level=logging.WARNING)


def get_targeted_group_id():
    with open(str(Path(__file__).parent.absolute()) + str('/config.json'), 'r', encoding='utf-8') as f:
        config = json.loads(f.read())
    return config['group_target']


def get_channel_hash(group_id, bot_api_id):
    channel_hash = session.query(ChannelHash).where(ChannelHash.channel_id == group_id).where(ChannelHash.bot_api_id == bot_api_id).first()
    return channel_hash


def get_user_hash(user_id, bot_api_id):
    user_hash = session.query(UserHash).where(UserHash.user_id == user_id).where(UserHash.bot_api_id == bot_api_id).first()
    return user_hash


def get_inviting_user():
    inviting_user = session.query(TelegramUser).where(TelegramUser.is_invited != True)\
        .where(TelegramUser.username != None).where(TelegramUser.has_photo != False)\
        .where(TelegramUser.last_seen != None).where(TelegramUser.invite_result == None)\
        .order_by(TelegramUser.last_seen.desc()).first()
    return inviting_user


def get_bot():
    bot = session.query(MyBot).where(MyBot.is_used != True)\
        .where(MyBot.is_paused != True).where(MyBot.note == 'invite_user')\
        .order_by(MyBot.id).first()
    if bot is None:
        session.query(MyBot).where(MyBot.note == 'invite_user').update({'is_used': False})
        session.commit()
        bot = session.query(MyBot).where(MyBot.is_used == False) \
            .where(MyBot.is_paused == False).where(MyBot.note == 'invite_user') \
            .order_by(MyBot.id).first()
    return bot


def get_bot_client(bot):
    telegram_client = TelegramClient(folder_session + bot.phone, bot.api_id, bot.api_hash)
    telegram_client.connect()

    if telegram_client.is_user_authorized():
        print(bot.phone + ' login success')
        return telegram_client
    else:
        print(bot.phone + ' login fail. Please re-run init_session')
        return None


def update_my_bot(bot, is_used, is_paused):
    bot.last_used = datetime.datetime.now()
    bot.is_used = is_used
    bot.is_paused = is_paused
    if is_paused is True:
        bot.paused_date = datetime.datetime.now()
    session.commit()


def update_invited_user(invited_user, is_invited, invite_result):
    invited_user.is_invited = is_invited
    invited_user.invite_result = invite_result
    invited_user.invited_date = datetime.datetime.now()
    session.commit()


def start_invite_user(is_first):
    my_bot = get_bot()
    client = get_bot_client(my_bot)

    group_target_id = get_targeted_group_id()
    current_channel_hash = get_channel_hash(group_target_id, my_bot.api_id)
    target_group_entity = InputPeerChannel(group_target_id, int(current_channel_hash.access_hash))

    user = get_inviting_user()

    if user is not None:
        try:
            print(str(datetime.datetime.now()) + ' add member: ' + str(user.user_id))
            current_user_hash = get_user_hash(user.user_id, my_bot.api_id)
            user_to_add = InputPeerUser(int(user.user_id), int(current_user_hash.access_hash))
            client(InviteToChannelRequest(target_group_entity, [user_to_add]))
            print(str(datetime.datetime.now()) + ' Add member ' + str(user.user_id) + ' success')
            update_my_bot(my_bot, True, False)
            update_invited_user(user, True, 'success')
        except PeerFloodError as e:
            print(str(datetime.datetime.now()) + " Error Fooling cmnr")
            update_my_bot(my_bot, True, True)
            update_invited_user(user, False, 'failed ' + str(e))
        except UserPrivacyRestrictedError as e:
            print(str(datetime.datetime.now()) + " Error Privacy")
            update_my_bot(my_bot, True, False)
            update_invited_user(user, False, 'failed ' + str(e))
            # if is_first:
            #     start_invite_user(False)
        except Exception as e:
            print(str(datetime.datetime.now()) + " Error other")
            print(e)
            update_my_bot(my_bot, True, False)
            update_invited_user(user, False, 'failed ' + str(e))


if 9 < datetime.datetime.now().hour < 22:
    start_invite_user(True)
