from datetime import timedelta, datetime

import api

import logging
import asyncio
import aiogram
import hashlib
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import InlineQuery, \
    InputTextMessageContent, InlineQueryResultArticle, InlineQueryResultPhoto
import sqlite3


global lists
lists = [i['ticker'] for i in api.get_all_events()]

# Устанавливаем уровень логов на DEBUG, чтобы видеть все сообщения об ошибках
logging.basicConfig(level=logging.DEBUG)

# Инициализируем бота и хранилище состояний
bot = Bot(token='6056598728:AAETWO9MCGyy3mg6Iq7lQ-WNrqgLaLggeDM')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Создаем подключение к базе данных SQLite
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Создаем таблицу users, если она не существует
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY
    )
''')
conn.commit()


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message, state: FSMContext):
    # Получаем id пользователя
    user_id = message.from_user.id

    cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()

    if result is None:
        cursor.execute('INSERT INTO users (id) VALUES (?)', (user_id,))
        conn.commit()
        await message.reply(f'Пользователь с id {user_id} добавлен в базу данных.')
    else:
        await message.reply(f'Пользователь с id {user_id} уже существует в базе данных.')

    # Очищаем состояние
    await state.finish()


@dp.message_handler(Command('exclude'))
async def exclude_user(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # Исключаем пользователя из базы данных по username
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()

    await message.reply(f'Пользователь {user_id} исключен из базы данных.')


async def send_time():
    while True:
        # Получаем текущее время
        current_time = datetime.now().strftime("%H:%M:%S")

        # Отправляем время всем пользователям
        try:
            cursor.execute('SELECT id FROM users')
            results = cursor.fetchall()

            users = [row[0] for row in results]

            for user_id in users:
                await bot.send_message(user_id, f"Текущее время: {current_time}")
        except Exception as e:
            logging.exception(f'Ошибка при отправке времени пользователям: {e}')

        # Ждем 30 минут перед следующей рассылкой

        await asyncio.sleep(30*60)


@dp.message_handler(Command('send_all'))
async def send_all_command(message: types.Message, state: FSMContext):
    # Получаем текст сообщения для рассылки
    print('asaaa')
    message_text = message.get_args()

    # Извлекаем список пользователей из базы данных
    cursor.execute('SELECT id FROM users')
    users = cursor.fetchall()

    # Отправляем сообщение каждому пользователю
    for user in users:
        user_id = user[0]
        try:
            await bot.send_message(user_id, message_text)
        except Exception as e:
            logging.exception(f'Ошибка при отправке сообщения по пользователю с id {user_id}: {e}')

        await message.reply('Рассылка завершена.')


@dp.message_handler(Command('graf'))
async def send_all_command(message: types.Message, state: FSMContext):
    df = api.table(message.text.split()[1])
    print(df, message.text)
    if df != '404':
        api.graf(df)
        with open('tsave3002.png', 'rb') as f:
            await message.answer_photo(f)
    else:
        await message.reply('404')


@dp.inline_handler()
async def inline_echo(inline_query: InlineQuery):
    # id affects both preview and content,
    # so it has to be unique for each result
    # (Unique identifier for this result, 1-64 Bytes)
    # you can set your unique id's
    # but for example i'll generate it based on text because I know, that
    # only text will be passed in this example
    text = inline_query.query or 'echo'
    input_content = InputTextMessageContent(text)
    result_id: str = hashlib.md5(text.encode()).hexdigest()

    print(lists)
    result = [InlineQueryResultPhoto(
        id=f'{element}',
        title=f'Result {element}',

        input_message_content=input_content,
        photo_url='',
    )
        for element in lists if text in element]

    # don't forget to set cache_time=1 for testing (default is 300s or 5m)
    await bot.answer_inline_query(inline_query.id, results=result, cache_time=1)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(send_time())
    try:
        aiogram.executor.start_polling(dp, skip_updates=True, loop=loop)
    finally:
        loop.close()
