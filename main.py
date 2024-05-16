# main.py

import sys
import logging
import asyncio
import time


from pytoniq_core import Address
from pytonconnect import TonConnect

import config
import nft_ownership
import cleaner
import search


from data.sales import sales
from data.nft import NftItems
from data import qr_code

from connector import get_connector

from aiogram.client.session.aiohttp import AiohttpSession

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InlineQueryResultPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder


logger = logging.getLogger(__file__)

dp = Dispatcher()
if config.PROXY is not None:
    session = AiohttpSession(proxy=config.PROXY)
    bot = Bot(config.TOKEN, session=session, parse_mode=ParseMode.HTML)
else:
    bot = Bot(config.TOKEN, parse_mode=ParseMode.HTML)

chat_links = {}
testnet = 't' if config.TESTNET else ''

rules_text = open("rules.txt", "r").read()

@dp.message(CommandStart())
async def command_start_handler(message: Message):
    chat_id = message.chat.id
    if chat_id < 0:
        await message.answer('Эта команда доступна только в личных сообщениях!')
        return
    print(chat_id)
    if chat_id < 0:
        return
    connector = get_connector(chat_id)
    connected = await connector.restore_connection()

    mk_b = InlineKeyboardBuilder()
    if connected:
        mk_b.button(text='Отключить', callback_data=f'{testnet}disconnect')
        await message.answer(text='Кошелёк уже подключен!', reply_markup=mk_b.as_markup())

    else:
        wallets_list = TonConnect.get_wallets()
        for wallet in wallets_list:
            mk_b.button(text=wallet['name'], callback_data=f'{testnet}connect:{wallet["name"]}')
        mk_b.adjust(1, )
        await message.answer(text='Выберите кошелёк для подключения:', reply_markup=mk_b.as_markup())

@dp.message(Command(f'{testnet}wallet'))
async def get_wallet(message: Message):
    chat_id = message.chat.id
    connector = get_connector(chat_id)
    connected = await connector.restore_connection()
    if connected:
        wallet_address = connector.account.address
        wallet_address = Address(wallet_address).to_str(is_bounceable=False)
        await message.answer(text=wallet_address)


@dp.message(Command(f'{testnet}chid'))
async def chid(message: Message):
    chat_id = message.chat.id
    await message.answer(text=str(chat_id))

@dp.message(Command(f'{testnet}clear'))
async def clear(message: Message):
    if message.chat.id != 983564480:
        return
    banned = await cleaner.clean(bot)
    await message.answer(text=f"Забанено {banned}")

@dp.message(Command(f'{testnet}rules'))
async def rules(message: Message):
    if message.chat.id != config.GROUP_CHAT_ID:
        return
    await message.answer(text=rules_text, parse_mode=ParseMode.HTML)

@dp.message(Command(f'{testnet}stats'))
async def stats(message: Message):
    # TODO add stats for side collections
    await sales.update()
    await message.answer(str(sales))


@dp.message(F.new_chat_members)
async def new_members_handler(message: Message):
    if message.chat.id != config.GROUP_CHAT_ID:
        return
    new_member = message.new_chat_members[0]
    print(chat_links)
    invite_link = chat_links.get(new_member.id, None)
    if invite_link is None:
        await bot.ban_chat_member(
            chat_id=config.GROUP_CHAT_ID,
            user_id=new_member.id
        )
    else:
        await bot.revoke_chat_invite_link(chat_id=config.GROUP_CHAT_ID, invite_link=invite_link)
        await bot.send_message(message.chat.id, f"Добро пожаловать, {new_member.first_name}! Пожалуйста, ознакомьтесь с правилами: /rules.")


async def connect_wallet(message: Message, wallet_name: str):
    if message.chat.id < 0:
        await message.answer('Эта команда доступна только в личных сообщениях!')
        return
    connector = get_connector(message.chat.id)

    wallets_list = connector.get_wallets()
    wallet = None

    for w in wallets_list:
        if w['name'] == wallet_name:
            wallet = w

    if wallet is None:
        raise Exception(f'Неизвестный кошелёк: {wallet_name}')

    generated_url = await connector.connect(wallet)

    img = qr_code.generate(generated_url)
    file = BufferedInputFile(file=img.getvalue(), filename='qrcode')

    mk_b = InlineKeyboardBuilder()
    mk_b.button(text='Подключить', url=generated_url)

    await message.answer_photo(photo=file, caption='Подключите кошелёк в течение 3 минут', reply_markup=mk_b.as_markup())

    for i in range(1, 180):
        await asyncio.sleep(1)
        if connector.connected:
            if connector.account.address:
                wallet_address = connector.account.address
                wallet_address = Address(wallet_address).to_str(is_bounceable=False)
                collections = await nft_ownership.check(wallet_address)
                await message.answer(f'Вы успешно подключились с адресом <code>{wallet_address}</code>.')
                for collection in collections:
                    bot_message = f'Вы являетесь владельцем NFT из коллекции {collection.name}. Ссылка на вход в беседу действительна 1 минуту.'
                    link = await bot.create_chat_invite_link(
                        chat_id=collection.chat_id,
                        name=str(message.chat.id),
                        expire_date=int(time.time()+60),
                        member_limit=1
                        )
                    chat_links[message.chat.id] = link.invite_link
                    print(chat_links)
                    mk_b = InlineKeyboardBuilder()
                    mk_b.button(text='Войти в беседу', url=link.invite_link)
                    await message.answer(bot_message, reply_markup=mk_b.as_markup())
                    logger.info(f'Connected with address: {wallet_address}')
                if len(collections) == 0:
                    bot_message = f'Вы <b>не являетесь</b> владельцем NFT из коллекции Soviet Girls. Приобрести NFT: https://getgems.io/sovietgirls.'
                    mk_b = InlineKeyboardBuilder()
                    mk_b.button(text='Отключить кошелёк', callback_data=f'{testnet}disconnect')
                    await message.answer(bot_message, reply_markup=mk_b.as_markup())
                    logger.info(f'Connected with address: {wallet_address}')
            return

    mk_b = InlineKeyboardBuilder()
    mk_b.button(text='Старт', callback_data=f'{testnet}start')
    await message.answer('Время для подключения вышло!', reply_markup=mk_b.as_markup())


async def disconnect_wallet(message: Message):
    if message.chat.id < 0:
        await message.answer('Эта команда доступна только в личных сообщениях!')
        return
    connector = get_connector(message.chat.id)
    await connector.restore_connection()
    try:
        await connector.disconnect()
    except:
        pass
    await message.answer('Вы отключили свой кошелёк!')


@dp.callback_query(lambda call: True)
async def main_callback_handler(call: CallbackQuery):
    await call.answer()
    message = call.message
    data = call.data
    if data == f"{testnet}start":
        await command_start_handler(message)
    elif data == f'{testnet}disconnect':
        await disconnect_wallet(message)
    else:
        data = data.split(':')
        if data[0] == f'{testnet}connect':
            await connect_wallet(message, data[1])


@dp.inline_query()
async def inline_query(inline_query: types.InlineQuery):
    chat_id = inline_query.from_user.id
    connector = get_connector(chat_id)
    connected = await connector.restore_connection()
    if connected:
        wallet_address = connector.account.address
        wallet_address = Address(wallet_address).to_str(is_bounceable=False)
    else:
        return
    text = inline_query.query or '-_-_-'
    inline_query.answer
    print(text)
    _i = 0
    content = []
    if text != "-_-_-":
        results = search.find(text)
        for result in results:
            if _i == 10:
                break
            price, rarity = await search.get_item(result['address'])
            text = f"<b>{result['name']}</b> ✅\nРедкость: {rarity}/283"
            if price:
                text += f"\n<b>{price} TON</b>"
            mk_b = InlineKeyboardBuilder()
            mk_b.button(text='Открыть в GetGems', url=f"https://getgems.io/nft/{result['address']}")
            content.append(
                InlineQueryResultPhoto(
                    id=str(_i),
                    photo_url=result['content']['image']['sized'],
                    thumbnail_url=result['content']['image']['sized'],
                    title=result['name'],
                    reply_markup=mk_b.as_markup(),
                    caption=text,
                    parse_mode=ParseMode.HTML
                )
            )
            _i += 1
        await bot.answer_inline_query(inline_query.id, results=content)

    
    nft_parser = NftItems(wallet_address)
    nft_items = await nft_parser.get()
    content = []
    _i = 0
    for item in nft_items:
        if _i == 10:
            break
        mk_b = InlineKeyboardBuilder()
        mk_b.button(text='Открыть в GetGems', url=f"https://getgems.io/nft/{item.address}")
        verify = "✅" if item.verify else ""
        text = f"<b>{item.name}</b> {verify}\nРедкость: {item.rarity}/283"
        if item.price:
            text += f"\n<b>{item.price} TON</b>"
        content.append(
            InlineQueryResultPhoto(
                id=str(_i),
                photo_url=item.image,
                thumbnail_url=item.image,
                title=item.name,
                reply_markup=mk_b.as_markup(),
                caption=text,
                parse_mode=ParseMode.HTML
            )
        )
        _i += 1
    await bot.answer_inline_query(inline_query.id, results=content)


async def main() -> None:
    await bot.delete_webhook(drop_pending_updates=True)  # skip_updates = True
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
