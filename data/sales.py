import aiohttp

query = """
query NftCollectionByAddress($address: String!, $userAddress: String!) {
  nftCollectionByAddress(address: $address) {
    approximateHoldersCount
    approximateItemsCount
    
  }
  alphaNftCollectionStats(address: $address) {
    floorPrice
    totalVolumeSold
  }
  userStats(userAddress: $userAddress) {
    tradingVolume
  }
}
"""

json_data = {
    'query': query,
    'variables': {
        "address": "EQBAS1oQQyLgHLTV7lg31yHT8FIbPM-Lsa2uMm8JDRi3WCwk",
        "userAddress": "EQBHxY02iPyaVa5KSqebug__2iL1ngT4PRCEIzPDFMKcUZqz"
    },
    'operationName': 'NftCollectionByAddress',
}

endpoint = "https://api.getgems.io/graphql"


class Sales:
    def __init__(self):
        self.owners = 0
        self.items = 0
        self.floor = 0
        self.volume = 0

    async def update(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=json_data) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200:
                    print(f"Error: {resp.status}")
                    print(f"Error: {data}")
                    return
                
        volume = int(data['data']['alphaNftCollectionStats']['totalVolumeSold'])
        user_stats_volume = int(data['data']['userStats']['tradingVolume'])
        volume += user_stats_volume
        volume += 24000000000 # получено с пресейла
        if volume == "0":
            volume = 0
        else:
            
            volume = int(str(volume)[:-9])

        self.owners = int(data['data']['nftCollectionByAddress']['approximateHoldersCount'])
        self.items = int(data['data']['nftCollectionByAddress']['approximateItemsCount'])
        self.floor = int(data['data']['alphaNftCollectionStats']['floorPrice'])
        self.volume = volume

    def __str__(self):
        return f"💎 Флор: {self.floor}\n👥 Владельцев: {self.owners}\n🏦 Оборот: {self.volume}"
        

sales = Sales()
sales.update()
