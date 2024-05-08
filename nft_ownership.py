import asyncio
import requests
import config


async def check(address: str) -> bool:
    _t = 0
    while True:
        if _t == 10:
            raise Exception("Check limit")
            
        url = f'https://tonapi.io/v2/accounts/{address}/nfts'
        params = {
            'collection': config.COLLECTION,
            'limit': 1,
            'offset': 0,
            'indirect_ownership': 1
        }
        response = requests.get(url=url, params=params)
        response = response.json()
        print(response)
        try:
            if response['error'] == 'rate limit: free tier':
                await asyncio.sleep(3)
                _t += 1
        except KeyError:
            pass
        return len(response['nft_items']) != 0