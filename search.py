
import json
import aiohttp
from pytoniq_core import Address

import config

with open('collection_data.json', 'r') as file:
    collection_data = json.load(file)


query_by_item = """
query HistoryNftItem($address: String!, $first: Int!) {
  historyNftItem(address: $address, first: $first) {
    items {
      nft {
        ownerAddress
        sale {
          ... on NftSaleFixPrice {
            fullPrice
          }
        }
        rarityRank
      }
    }
  }
}
"""


def find(query: str):
    results = []
    for item in collection_data:
        if query in item['name'].lower():
            results.append(item)
    return results


async def get_item(address: str):
    
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.getgems.io/graphql", json={'query': query_by_item, 'variables': {'address': address, 'first': 1}}) as response:
            data = await response.json()
            data = data['data']['historyNftItem']['items'][0]['nft']
            owner_address = data['ownerAddress']
            if data['sale'] is not None:
                price = int(data['sale']['fullPrice'][:-9])
            else:
                price = None
            rarity = data['rarityRank']
        
        return price, rarity
