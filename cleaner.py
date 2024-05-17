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
        try:
            id = int(str(keys[i]).split("b'")[1].split('connection')[0])
        except ValueError:
            continue
        connections.append([id, values[i]])
    return connections

async def clean(bot: Bot):
    connections = await get_connections()
    i = 0
    steps = len(connections)
    print(f"Checking {steps} connections")
    for connection in connections:
        print(f"Connection {i+1}/{steps}")
        user_id = connection[0]
        connector = get_connector(user_id)
        connected = await connector.restore_connection()
        if connected is False:
            try:
                user = await bot.get_chat_member(group_chat_id, user_id)
                if user.status == 'member':
                    await bot.send_message(group_chat_id, "Пользователь разорвал подключение с ботом! Исключаю из чата c правом на возвращение.")
            except Exception:
                pass
            await bot.ban_chat_member(group_chat_id, user_id)
            await bot.unban_chat_member(group_chat_id, user_id)
            await client.delete(str(user_id)+'connection')

            i += 1
            try:
                await bot.send_message(user_id, f"Вы были исключены из чата владельцев {collection.name}, так как разорвали подключение. Подключиться снова: /start")
            except:
                pass
        else:
            wallet_address = connector.account.address
            wallet_address = Address(wallet_address).to_str(is_bounceable=False)
            collections = await nft_ownership.check(wallet_address)
            if len(collections) > 0:
                continue
            else:
                for collection in nft_ownership.side_collections:
                    user = await bot.get_chat_member(collection.chat_id, user_id)
                    try: 
                        if user.status == 'member':
                            await bot.send_message(collection.chat_id, f"Пользователь не имеет NFT из коллекции {collection.name}! Исключаю из чата c правом на возвращение.")
                    except Exception:
                        pass
                    await bot.send_message(user_id, f"Вы исключены из закрытого чата владельцев {collection.name}, так как не имеете NFT из данной коллекции.")
                    await bot.ban_chat_member(collection.chat_id, user_id)
                    await bot.unban_chat_member(collection.chat_id, user_id)
                    await client.delete(str(user_id)+'connection')
                    i += 1
    return i
