API_TOKEN = '6056598728:AAETWO9MCGyy3mg6Iq7lQ-WNrqgLaLggeDM'

import hashlib
import logging

from aiogram import Bot, Dispatcher, executor
from aiogram.types import InlineQuery, \
    InputTextMessageContent, InlineQueryResultArticle



logging.basicConfig(level=logging.DEBUG)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


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
    result = []
    if text in 'LKOH':
        item = InlineQueryResultArticle(
            id='1',
            title='Result LKOH',

            input_message_content=input_content,
        )
        result.append(item)
    if text in 'LHOSHENKO':
        item2 = InlineQueryResultArticle(
            id='2',
            title='Result LHOSHENKO',
            input_message_content=input_content,
        )
        result.append(item2)
    if text in 'LEPS':
        item3 = InlineQueryResultArticle(
            id='3',
            title='Result LEPS',
            input_message_content=input_content,
        )
        result.append(item3)
    if text == '4':
        item4 = InlineQueryResultArticle(
            id='4',
            title='Result 4',
            input_message_content=input_content,
        )
        result.append(item4)


    # don't forget to set cache_time=1 for testing (default is 300s or 5m)
    await bot.answer_inline_query(inline_query.id, results=result, cache_time=1)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)