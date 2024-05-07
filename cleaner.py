from aiogram import Bot
from pytoniq_core import Address

from db_connection import client
from connector import get_connector

import nft_ownership

group_chat_id = -1002137181356

async def get_connections():
    connections = []
    keys = await client.keys('*connection')
    values = await client.mget(keys)
    for i in range(len(keys)):
        id = int(str(keys[i]).split("b'")[1].split('connection')[0])
        connections.append([id, values[i]])
    return connections

async def clean(bot: Bot):
    connections = await get_connections()
    i = 0
    for connection in connections:
        user_id = connection[0]
        connector = get_connector(user_id)
        connected = await connector.restore_connection()
        if connected is False:
            await bot.send_message(group_chat_id, "Пользователь разорвал подключение!")
            await bot.ban_chat_member(group_chat_id, user_id)
            await bot.unban_chat_member(group_chat_id, user_id)
            await client.delete(str(user_id)+'connection')

            i += 1
            try:
                await bot.send_message(user_id, "Вы были исключены из чата, так как разорвали подключение.")
            except:
                pass
        else:
            wallet_address = connector.account.address
            wallet_address = Address(wallet_address).to_str(is_bounceable=False)
            if nft_ownership.check(wallet_address):
                continue
            else:
                await bot.send_message(group_chat_id, "Пользователь не имеет NFT из коллекции!")
                await bot.ban_chat_member(group_chat_id, user_id)
                await bot.unban_chat_member(group_chat_id, user_id)
                await client.delete(str(user_id)+'connection')
                i += 1
                try:
                    await bot.send_message(user_id, "Вы были исключены из чата, так как не имеете NFT из коллекции.")
                except:
                    pass
    return i
