from db_connection import client

class ChatLinksStorage:

    def __init__(self) -> None:
        pass

    def _get_key(self, key: str):
        return 'link_' + key
    
    async def set_item(self, key: str, value: str):
        await client.set(name=self._get_key(key), value=value)

    async def get_item(self, key: str, default_value: str = None):
        value = await client.get(name=self._get_key(key))
        return value.decode() if value else default_value

    async def remove_item(self, key: str):
        await client.delete(self._get_key(key))

chat_link_storage = ChatLinksStorage()