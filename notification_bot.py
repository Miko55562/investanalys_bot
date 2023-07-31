from datetime import datetime
import asyncio
import aiogram
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import InlineQuery, InputTextMessageContent, InlineQueryResultArticle
from aiogram.dispatcher.filters.state import State, StatesGroup

import db_helper
import ta_helper


class States(StatesGroup):
    WAITING_FOR_TICKER = State()


logging.basicConfig(level=logging.DEBUG)


bot = Bot(token='6056598728:AAETWO9MCGyy3mg6Iq7lQ-WNrqgLaLggeDM')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message, state: FSMContext):
    # Получаем id пользователя
    user_id = message.from_user.id
    username = message.from_user.username

    create_user_result = await db_helper.create_user(user_id, username)

    if create_user_result is not None:
        
        await message.reply(f'Пользователь с id {user_id} добавлен в базу данных.')
    else:
        await message.reply(f'Пользователь с id {user_id} уже существует в базе данных.')

    # Очищаем состояние
    await state.finish()


@dp.message_handler(Command('exclude'))
async def exclude_user(message: types.Message):
    user_id = message.from_user.id

    await db_helper.delete_user(user_id)

    await message.reply(f'Пользователь {user_id} исключен из базы данных.')


async def send_time():
    while True:
        # Получаем текущее время
        current_time = datetime.now().strftime("%H:%M:%S")

        # Отправляем время всем пользователям
        try:
            results = await db_helper.get_all_users()
            print(results)
            users = [row['external_id'] for row in results]

            for user_id in users:
                await bot.send_message(user_id, f"Текущее время: {current_time}")
        except Exception as e:
            logging.exception(f'Ошибка при отправке времени пользователям: {e}')

        # Ждем 30 минут перед следующей рассылкой

        await asyncio.sleep(30*60)


@dp.message_handler(Command('send_all'))
async def send_all_command(message: types.Message):
    message_text = message.get_args()

    # Извлекаем список пользователей из базы данных
    users = await db_helper.get_all_users()

    # Отправляем сообщение каждому пользователю
    for user in users:
        user_id = user['external_id']
        try:
            await bot.send_message(user_id, message_text)
        except Exception as e:
            logging.exception(f'Ошибка при отправке сообщения по пользователю с id {user_id}: {e}')

        await message.reply('Рассылка завершена.')


@dp.message_handler(Command('graf'))
async def send_all_command(message: types.Message):
    await message.reply("Отправь мне тикер бумаги которую вы хотите получить для этого "
                        "воспользуйтесь поиском с помощью @TradingBotification_bot ")
    await States.WAITING_FOR_TICKER.set()


@dp.message_handler(state=States.WAITING_FOR_TICKER)
async def process_name(message: types.Message, state: FSMContext):
    print(message.text.strip().split())
    instrument = await db_helper.get_instrument(message.text.strip().split()[0].upper())
    if instrument is not False:
        await message.answer_photo(instrument['logo_url'], f"{instrument['name']}\n\nTicker: {instrument['ticker']}"
                                                           f"\nISIN: {instrument['isin']}\nFIGI: {instrument['figi']}"
                                                           f"\n\n{instrument['info']}")
        try:
            df = ta_helper.table(instrument['figi'])
            print(df, message.text)
            ta_helper.graf(df, instrument)
            with open('tsave3002.png', 'rb') as f:
                await message.answer_photo(f)
            await state.finish()
        except:
            await message.reply('Извините не можем постраить график этой бумаги (')
    else:
        await message.reply("Неверное имя инструмента")


@dp.inline_handler(state=States.WAITING_FOR_TICKER)
async def inline_echo(inline_query: InlineQuery):
    # id affects both preview and content,
    # so it has to be unique for each result
    # (Unique identifier for this result, 1-64 Bytes)
    # you can set your unique id's
    # but for example i'll generate it based on text because I know, that
    # only text will be passed in this example
    text = inline_query.query or 'echo'
    # input_content = InputTextMessageContent(text)
    # result_id: str = hashlib.md5(text.encode()).hexdigest()
    response = await db_helper.search_instrument(text)
    print(response)
    result = [InlineQueryResultArticle(
        id=f'{instrument["ticker"]}',
        title=f'{instrument["name"]}',
        input_message_content=InputTextMessageContent(message_text=f'{instrument["ticker"]}\nФиги: '
                                                                   f'{instrument["figi"]}\nИсин: {instrument["isin"]}'),
        thumb_url=f'{instrument["logo_url"]}',
        url=f'{instrument["logo_url"]}',
        hide_url=True,

    ) for instrument in response]

    # don't forget to set cache_time=1 for testing (default is 300s or 5m)
    await inline_query.answer(result, cache_time=1, is_personal=True)
dp.register_inline_handler(inline_echo)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(send_time())
    try:
        aiogram.executor.start_polling(dp, skip_updates=True, loop=loop)
    finally:
        loop.close()
