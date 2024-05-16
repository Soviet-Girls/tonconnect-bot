# config.py

from os import environ as env

from dotenv import load_dotenv
load_dotenv()

TOKEN = env['TOKEN']
MANIFEST_URL = env['MANIFEST_URL']

COLLECTION = env['COLLECTION']
COLLECTION_NAME = env['COLLECTION_NAME'] = "Soviet Girls TON"

REDIS_HOST = env['REDIS_HOST']
REDIS_PORT = env['REDIS_PORT']
REDIS_USERNAME = env['REDIS_USERNAME']
REDIS_PASSWORD = env['REDIS_PASSWORD']
TESTNET = env['TESTNET'] == 'False'

# lead chat id
GROUP_CHAT_ID = int(env['GROUP_CHAT_ID'])

PROXY = env['PROXY'] = ''
if PROXY == '':
    PROXY = None