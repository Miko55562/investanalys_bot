from datetime import datetime
import asyncio
import aiogram
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import InlineQuery, InputTextMessageContent, InlineQueryResultArticle, CallbackQuery
from aiogram.dispatcher.filters.state import State, StatesGroup
from tinkoff.invest import CandleInterval
import db_helper
import ta_helper
import markup


class Instrument(StatesGroup):
    ticker = State()
    interval = State()


logging.basicConfig(level=logging.DEBUG)
logging.getLogger('matplotlib.font_manager').disabled = True


bot = Bot(token='6056598728:AAETWO9MCGyy3mg6Iq7lQ-WNrqgLaLggeDM')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start'], state="*")
async def start_command(message: types.Message):
    create_user_result = await db_helper.create_user(str(message.from_user.id), message.from_user.username)

    if create_user_result:
        await message.reply(f'User id {message.from_user.id} add in database.', reply_markup=markup.markup_main())
    else:
        await message.reply(f'User id {message.from_user.id} already in database.', reply_markup=markup.markup_main())


@dp.message_handler(Command('exclude'), state="*")
async def exclude_user(message: types.Message):
    await db_helper.delete_user(message.from_user.id)

    await message.reply(f'Пользователь {message.from_user.id} исключен из базы данных.')

'''
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
'''


@dp.message_handler(Command('send_all'), state="*")
async def send_all_command(message: types.Message):
    users = await db_helper.get_all_users()

    for user in users:
        try:
            await bot.send_message(user["external_id"], message.get_args())
        except Exception as e:
            logging.exception(f'Ошибка при отправке сообщения по пользователю с id {user["external_id"]}: {e}')

        await message.reply('Рассылка завершена.')


@dp.message_handler(Command('graf'), state="*")
async def send_all_command(message: types.Message):
    await message.reply("Отправь мне тикер бумаги которую вы хотите получить для этого "
                        "воспользуйтесь поиском с помощью команды <code>@TradingBotification_bot</code>\n\n"
                        "Например <code>@TradingBotification_bot Сбер Банк </code>", parse_mode=types.ParseMode.HTML)
    await Instrument.ticker.set()


@dp.message_handler(state=Instrument.ticker)
async def process_name(message: types.Message, state: FSMContext):
    print(message.text.strip().split())
    instrument = await db_helper.get_instrument(message.text.strip().split()[0].upper())
    if instrument is not False:
        async with state.proxy() as data:
            data['instrument'] = instrument
        await message.answer_photo(instrument['logo_url'], f"{instrument['name']}\n\nTicker: {instrument['ticker']}"
                                                           f"\nISIN: {instrument['isin']}\nFIGI: {instrument['figi']}"
                                                           f"\n\n{instrument['info']}", reply_markup=markup.markup_interval())
        await message.answer('Выбирите временной инервал свечей:')
        await Instrument.interval.set()
    else:
        await message.reply("Неверное имя инструмента", reply_markup=markup.markup_main())


@dp.message_handler(state=Instrument.interval)
async def process_interval(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        print('PROCESS_INTERVAL')
        instrument = data['instrument']
        print(data['instrument'])
        if message.text == "4 hour":
            days=60
            interval=CandleInterval.CANDLE_INTERVAL_4_HOUR
        elif message.text == "1 day":
            days=120
            interval = CandleInterval.CANDLE_INTERVAL_DAY
        elif message.text == "1 wick":
            days = 720
            interval = CandleInterval.CANDLE_INTERVAL_WEEK
        try:
            df = ta_helper.table(instrument['figi'], days=days, interval=interval)
            print(df, message.text)
            ta_helper.graf(df, instrument)
            with open('tsave3002.png', 'rb') as f:
                await message.answer_photo(f, reply_markup=markup.markup_main())
            await state.finish()
        except:
            await message.answer('Извините не можем постраить график этой бумаги (')


@dp.inline_handler(state=Instrument.ticker)
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
    # loop.create_task(send_time())
    try:
        aiogram.executor.start_polling(dp, skip_updates=True, loop=loop)
    finally:
        loop.close()
