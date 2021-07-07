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
from sqlalchemy.orm import Session
from tables.my_bots import MyBot

logging.basicConfig(level=logging.WARNING)
load_dotenv()

engine = create_engine('mysql+pymysql://'+os.getenv('DB_USERNAME')+':'+urllib.parse.quote(os.getenv('DB_PASS'))+'@'+os.getenv('DB_URL')+':'+os.getenv('DB_PORT')+'/'+os.getenv('DB_SCHEMA')+'')
db_conn = engine.connect()
session = Session(engine, future=True)

target_date = datetime.now() - timedelta(days=1)
paused_bots = session.query(MyBot).where(MyBot.is_paused == True).where(MyBot.paused_date < target_date).all()
try:
    for bot in paused_bots:
        bot.is_paused = False
        session.commit()
except Exception as e:
    print('Resuming bot error')
    print(e)
