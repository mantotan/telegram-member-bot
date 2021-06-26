import os
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient, connection
import logging
from telethon import sync, TelegramClient, events
from tables.my_bots import MyBot
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

load_dotenv()

engine = create_engine('mysql+pymysql://'+os.getenv('DB_USERNAME')+':'+urllib.parse.quote(os.getenv('DB_PASS'))+'@'+os.getenv('DB_URL')+':'+os.getenv('DB_PORT')+'/'+os.getenv('DB_SCHEMA')+'')
db_conn = engine.connect()
session = Session(engine, future=True)

logging.basicConfig(level=logging.WARNING)

my_bots = session.query(MyBot).all()

folder_session = str(Path(__file__).parent.absolute()) + str('/session/')

for account in my_bots:
	api_id = account.api_id
	api_hash = account.api_hash
	phone = account.phone
	print(phone)

	client = TelegramClient(folder_session + phone, api_id, api_hash)
	client.start()
	if client.is_user_authorized():
		print('Login success')
	else:
		print('Login fail')
	client.disconnect()