# main.py

import sys
import logging
import asyncio
import time
import qrcode
from io import BytesIO

from pytoniq_core import Address
from pytonconnect import TonConnect

import config
import nft_ownership
import cleaner

from connector import get_connector

from aiogram.client.session.aiohttp import AiohttpSession

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

group_chat_id = -1002137181356

logger = logging.getLogger(__file__)

dp = Dispatcher()
session = AiohttpSession(proxy='socks5://35.229.105.131:11080')
bot = Bot(config.TOKEN, session=session, parse_mode=ParseMode.HTML)

chat_links = {}

with open("rules.txt", "r") as file:
    rules = file.read()

@dp.message(CommandStart())
async def command_start_handler(message: Message):
    chat_id = message.chat.id
    print(chat_id)
    if chat_id < 0:
        return
    connector = get_connector(chat_id)
    connected = await connector.restore_connection()

    mk_b = InlineKeyboardBuilder()
    if connected:
        mk_b.button(text='Отключить', callback_data='disconnect')
        await message.answer(text='Кошелёк уже подключен!', reply_markup=mk_b.as_markup())

    else:
        wallets_list = TonConnect.get_wallets()
        for wallet in wallets_list:
            mk_b.button(text=wallet['name'], callback_data=f'connect:{wallet["name"]}')
        mk_b.adjust(1, )
        await message.answer(text='Выберите кошелёк для подключения:', reply_markup=mk_b.as_markup())

@dp.message(Command('wallet'))
async def get_wallet(message: Message):
    chat_id = message.chat.id
    connector = get_connector(chat_id)
    connected = await connector.restore_connection()
    if connected:
        wallet_address = connector.account.address
        wallet_address = Address(wallet_address).to_str(is_bounceable=False)
        await message.answer(text=wallet_address)


@dp.message(Command('chid'))
async def chid(message: Message):
    chat_id = message.chat.id
    await message.answer(text=str(chat_id))

@dp.message(Command('clear'))
async def clear(message: Message):
    if message.chat.id != 983564480:
        return
    banned = await cleaner.clean(bot)
    await message.answer(text=f"Забанено {banned}")
    


@dp.message(F.new_chat_members)
async def new_members_handler(message: Message):
    new_member = message.new_chat_members[0]
    print(chat_links)
    invite_link = chat_links.get(new_member.id, None)
    if invite_link is None:
        await bot.ban_chat_member(
            chat_id=group_chat_id,
            user_id=new_member.id
        )
    else:
        await bot.revoke_chat_invite_link(chat_id=group_chat_id, invite_link=invite_link)
        await bot.send_message(message.chat.id, f"Добро пожаловать, {new_member.first_name}! Пожалуйста, ознакомьтесь с правилами в закрепленном сообщении.")


async def connect_wallet(message: Message, wallet_name: str):
    if message.chat.id < 0:
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

    img = qrcode.make(generated_url)
    stream = BytesIO()
    img.save(stream)
    file = BufferedInputFile(file=stream.getvalue(), filename='qrcode')

    mk_b = InlineKeyboardBuilder()
    mk_b.button(text='Подключить', url=generated_url)

    await message.answer_photo(photo=file, caption='Подключите кошелёк в течение 3 минут', reply_markup=mk_b.as_markup())

    for i in range(1, 180):
        await asyncio.sleep(1)
        if connector.connected:
            if connector.account.address:
                wallet_address = connector.account.address
                wallet_address = Address(wallet_address).to_str(is_bounceable=False)
                owner = await nft_ownership.check(wallet_address)
                if owner:
                    bot_message = 'Вы являетесь владельцем NFT из коллекции Soviet Girls. Ссылка на вход в беседу действительна 1 минуту.'
                    link = await bot.create_chat_invite_link(
                        chat_id=group_chat_id,
                        name=str(message.chat.id),
                        expire_date=int(time.time()+60),
                        member_limit=1
                        )
                    chat_links[message.chat.id] = link.invite_link
                    print(chat_links)
                    mk_b = InlineKeyboardBuilder()
                    mk_b.button(text='Войти в беседу', url=link.invite_link)
                else:
                    bot_message = 'Вы <b>не являетесь</b> владельцем NFT из коллекции Soviet Girls.'
                    mk_b = InlineKeyboardBuilder()
                    mk_b.button(text='Отключить кошелёк', callback_data='disconnect')
                await message.answer(f'Вы подключены с адресом <code>{wallet_address}</code>. '+bot_message, reply_markup=mk_b.as_markup())
                logger.info(f'Connected with address: {wallet_address}')
            return

    mk_b = InlineKeyboardBuilder()
    mk_b.button(text='Старт', callback_data='start')
    await message.answer('Время для подключения вышло!', reply_markup=mk_b.as_markup())


async def disconnect_wallet(message: Message):
    if message.chat.id < 0:
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
    if data == "start":
        await command_start_handler(message)
    elif data == 'disconnect':
        await disconnect_wallet(message)
    else:
        data = data.split(':')
        if data[0] == 'connect':
            await connect_wallet(message, data[1])


async def main() -> None:
    await bot.delete_webhook(drop_pending_updates=True)  # skip_updates = True
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
