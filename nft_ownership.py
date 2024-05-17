import asyncio
import aiohttp
import config
import json
import traceback
import logging
import aiofiles

class Collection:
    def __init__(self, collection):
        self.name = str(collection['name'])
        self.address = str(collection['address'])
        self.chat_id = int(collection['chat_id'])


def load() -> list[Collection]:
    side_collections = []
    with open('side_collections.json', 'r') as f:
        side_collections_raw = list(json.load(f))
    try:
        import requests
        url = 'https://raw.githubusercontent.com/Soviet-Girls/tonconnect-bot/main/side_collections.json'
        response = requests.get(url)
        side_collections_raw_online = list(json.loads(response.text))
        if len(side_collections_raw_online) > len(side_collections_raw):
            side_collections_raw = side_collections_raw_online
    except Exception as e:
        logging.exception(e)
    for collection in side_collections_raw:
        collection = Collection(collection)
        side_collections.append(collection)
    return side_collections

side_collections = []
try:
    side_collections = load()
    print(f"{len(side_collections)}  collections loaded")
except Exception as e:
    logging.exception(e)

async def check(address: str) -> list[Collection]:
    collections = []

    side_collections = []
    try:
        side_collections = load()
        print(f"{len(side_collections)}  collections loaded")
    except Exception as e:
        logging.exception(e)
    # добавляем основную коллекцию и ставим её на первое место
    side_collections.append(
        Collection({
            'name': config.COLLECTION_NAME,
            'address': config.COLLECTION,
            'chat_id': config.GROUP_CHAT_ID,
        })
    )
    available_collections = [side_collections[-1]] + side_collections[:-1]

    async with aiohttp.ClientSession() as session:
        for collection in available_collections:
            url = f'https://tonapi.io/v2/accounts/{address}/nfts'
            params = {
                'collection': collection.address,
                'limit': 1,
                'offset': 0,
                'indirect_ownership': 1
            }
            _t = 0
            while _t < 5:
                async with session.get(url=url, params=params) as response:
                    response = await response.json()
                    if response.get('error') == 'rate limit: free tier':
                        await asyncio.sleep(3)
                        _t += 1
                        continue
                    if len(response['nft_items']) > 0:
                        collections.append(collection)
                        break
    logging.info(str(collections))
    return collections