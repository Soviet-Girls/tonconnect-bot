import requests
import config


def check(address: str) -> bool:
    url = f'https://tonapi.io/v2/accounts/{address}/nfts'
    params = {
        'collection': config.COLLECTION,
        'limit': 1,
        'offset': 0,
        'indirect_ownership': 1
    }
    response = requests.get(url=url, params=params)
    response = response.json()
    return len(response['nft_items']) != 0