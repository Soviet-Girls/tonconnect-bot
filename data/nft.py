import aiohttp

query_by_owner = """
query NftItemsByOwner($ownerAddress: String!, $first: Int!, $width: Int!, $height: Int!) {
  nftItemsByOwner(ownerAddress: $ownerAddress, first: $first) {
    items {
      address
      name
      rarityRank
      content {
        ... on NftContentImage {
          image {
            sized(width: $width, height: $height)
          }
        }
      }
      sale {
        ... on NftSaleFixPrice {
          fullPrice
        }
      }
      collection {
        address
      }
    }
  }
}
"""



endpoint = "https://api.getgems.io/graphql"

class NftItem:
    def __init__(self, 
                 address: str,
                 collection: str,
                 name: str,
                 rarity: int,
                 image: str,
                 price: int = None,):
        self.address = address
        self.collection = collection
        self.name = name
        self.rarity = rarity
        self.image = image
        self.price = price
        if collection == "EQBAS1oQQyLgHLTV7lg31yHT8FIbPM-Lsa2uMm8JDRi3WCwk":
            self.verify = True
        else:
            self.verify = False

    def __str__(self):
        return f"{self.name}"


class NftItems:
    def __init__(self, address: str):
        self.json_data = {
            'query': query_by_owner,
            'variables': {
                "ownerAddress": address,
                "first": 100,
                "width": 500,
                "height": 500
            },
            'operationName': 'NftItemsByOwner',
        }

    async def get(self) -> list[NftItem]:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=self.json_data) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200:
                    print(f"Error: {resp.status}")
                    print(f"Error: {data}")
                    return
        
        items = []
        for item in data['data']['nftItemsByOwner']['items']:
            address = item['address']
            name = item['name']
            rarity = item['rarityRank']
            image = item['content']['image']['sized']
            collection = item['collection']['address']
            if item['sale'] is not None:
                price = int(item['sale']['fullPrice'][:-9])
            else:
                price = None
            items.append(NftItem(address, collection, name, rarity, image, price))

        return items
    
