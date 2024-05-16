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

async def load() -> list[Collection]:
    side_collections = []
    async with aiofiles.open('side_collections.json', mode='r') as f:
        side_collections_raw = list(json.load(await f.read()))
    try:
        url = 'https://raw.githubusercontent.com/Soviet-Girls/tonconnect-bot/main/side_collections.json'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                side_collections_raw_online = list(json.loads(await response.text()))
        if len(side_collections_raw_online) > len(side_collections_raw):
            side_collections_raw = side_collections_raw_online
    except Exception as e:
        logging.exception(e)
    for collection in side_collections_raw:
        collection = Collection(collection)
        side_collections.append(collection)
    return side_collections

_collections = []
try:
    side_collections = asyncio.run(load())
    print(f"{len(_collections)}  collections loaded")
except Exception as e:
    logging.exception(e)

async def check(address: str) -> list[Collection]:
    collections = []

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