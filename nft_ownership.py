import asyncio
import aiohttp
import config
import json
import traceback
import logging



class SideCollection:
    def __init__(self, collection):
        # name и adress -- str
        self.name = str(collection['name'])
        self.address = str(collection['address'])
        self.chat_id = int(collection['chat_id'])
        
def load() -> list[SideCollection]:
    side_collections = []
    side_collections_raw = list(json.load(open('side_collections.json')))
    try:
        import requests
        url = 'https://raw.githubusercontent.com/Soviet-Girls/tonconnect-bot/main/side_collections.json'
        side_collections_raw_online = list(json.loads(requests.get(url).text))
        if len(side_collections_raw_online) > len(side_collections_raw):
            side_collections_raw = side_collections_raw_online
    except:
        pass
    for collection in side_collections_raw:
        collection = SideCollection(collection)
        side_collections.append(collection)
    return side_collections

side_collections = []
try:
    side_collections = load()
    print(f"{len(side_collections)} side collections loaded")
except:
    traceback.print_exc()
    logging.error('ERROR LOADING SIDE COLLECTIONS!')


async def check(address: str) -> list[SideCollection]:
    url = f'https://tonapi.io/v2/accounts/{address}/nfts'
    collections = []
    _t = 0
    while True:
        if _t == 5:
            break
        params = {
            'collection': config.COLLECTION,
            'limit': 1,
            'offset': 0,
            'indirect_ownership': 1
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params) as response:
                response = await response.json()
                print(response)
                try:
                    if response['error'] == 'rate limit: free tier':
                        await asyncio.sleep(3)
                        _t += 1
                        continue
                except KeyError:
                    pass
                if len(response['nft_items']) > 0:
                    collections.append(SideCollection({'name': config.COLLECTION_NAME, 'address': config.COLLECTION, 'chat_id': config.GROUP_CHAT_ID}))
                    break
    
    for side_collection in side_collections:
        url = f'https://tonapi.io/v2/accounts/{address}/nfts'
        params = {
            'collection': side_collection.address,
            'limit': 1,
            'offset': 0,
            'indirect_ownership': 1
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params) as response:
                response = await response.json()
                if len(response['nft_items']) > 0:
                    collections.append(side_collection)

    return collections