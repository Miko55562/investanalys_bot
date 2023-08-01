import logging
import sqlite3
import re
import json
import asyncio
import ta_helper
from bs4 import BeautifulSoup
import requests

connect = sqlite3.connect('db.sqlite3', check_same_thread=False)
cursor = connect.cursor()


def inst_serializer(instrument):
    names = [column[0] for column in cursor.description]
    serialized_instruments = [{names[i]: row[i] for i in range(len(row))} for row in instrument]
    return serialized_instruments


async def user_serializer(user):
    fields = ['external_id', 'name']
    serialized_users = [{fields[i]: row[i] for i in range(len(row))} for row in user]
    return serialized_users[0]


async def get_all_users():
    rows = cursor.execute("SELECT * FROM bot_users;").fetchall()
    users = [{'name': row[0], 'external_id': row[1]} for row in rows]
    return users


async def create_user(external_id, name):
    cursor.execute("SELECT * FROM bot_users WHERE external_id=?", (external_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        # Пользователь с таким external_id уже существует, обновляем его имя
        cursor.execute("UPDATE bot_users SET name=? WHERE external_id=?", (name, external_id))
        connect.commit()
        return None
    else:
        # Пользователя с таким external_id еще нет, создаем новую запись
        cursor.execute("INSERT INTO bot_users (name, external_id) VALUES (?, ?)", (name, external_id))
        connect.commit()
        return True


async def delete_user(external_id):
    cursor.execute(f"DELETE FROM bot_users WHERE external_id=?", (external_id,))
    connect.commit()
    return True


async def get_user(external_id):
    rows = cursor.execute(f"SELECT * FROM bot_users WHERE external_id=?", (external_id,)).fetchall()
    user = [{'name': row[0], 'external_id': row[1]} for row in rows]
    return user


async def get_all_instruments():
    rows = cursor.execute("SELECT * FROM bot_instruments;").fetchall()
    instruments = [{'ticker': row[0], 'name': row[1]} for row in rows]
    return instruments


async def search_instrument(name):
    rows = cursor.execute("SELECT * FROM bot_instruments WHERE name COLLATE NOCASE LIKE '%' || ? || '%'",
                          ('%' + name + '%',)).fetchall()
    return inst_serializer(rows)
    # return inst_serializer(cursor.execute("SELECT * FROM bot_instruments WHERE LOWER(name) LIKE ?",
    # (f'%{name.lower()}%',)).fetchall())


async def get_instrument(ticker):
    cursor.execute("SELECT * FROM bot_instruments WHERE ticker LIKE ? COLLATE NOCASE", (f'%{ticker}%',))
    r = inst_serializer(cursor.fetchall())
    return r[0] if r != [] else False


async def main():
    print("TEST db_helper.py")
    await create_user(123456, 'Tom')
    users = await get_all_users()
    print(json.dumps(users))
    user = await get_user(123456)
    print(json.dumps(user))
    await delete_user(123456)
    user = await get_user(123456)
    print(json.dumps(user))
    users = await get_all_users()
    print(json.dumps(users))
    inst = await get_instrument('moex')
    print(inst)
    inst = await search_instrument('Лукойл')
    print(inst)


def get_logo(ticker, e_type, size=640):
    if e_type == 'shares':
        e_type = 'stocks'
    response = requests.get(f'https://www.tinkoff.ru/invest/{e_type}/{ticker}/')
    soup = BeautifulSoup(response.content, 'html.parser')
    script = soup.find('script', attrs={'id': '__TRAMVAI_STATE__'})
    try:
        if script is not None:
            json_objects = json.loads('[' + script.string + ']')
            print(json_objects[0]['stores']['investBrand'][f'{ticker}']['brandInfo'])
            return f'https://invest-brands.cdn-tinkoff.ru/' + str(json_objects[0]['stores']['investBrand']
                                                                  [f'{ticker}']['logoName'])[:-4] + f'x{size}.png'
    except:
        return 'except'


def get_info(ticker, e_type):
    if e_type == 'shares':
        e_type = 'stocks'
    response = requests.get(f'https://www.tinkoff.ru/invest/{e_type}/{ticker}/')
    soup = BeautifulSoup(response.content, 'html.parser')
    script = soup.find('script', attrs={'id': '__TRAMVAI_STATE__'})
    try:
        if script is not None:
            json_objects = json.loads('[' + script.string + ']')
            print(json_objects[0]['stores']['investBrand'][f'{ticker}']['brandInfo'])

            return json_objects[0]['stores']['investBrand'][f'{ticker}']['brandInfo']
    except Exception as e:
        logging.exception(e)


def get_or_create_instrument(id, name, info, ticker, method, figi, isin, currency, logo_url):
    cursor.execute("SELECT * FROM bot_instruments WHERE ticker=?", (ticker.upper(),))
    r = cursor.fetchone()
    if r:
        cursor.execute(
            "UPDATE bot_instruments SET id=?, name=?, info=?, ticker=?, method=?, figi=?, isin=?, currency=?, "
            "logo_url=? WHERE ticker=?",
            (id, name, info, ticker, method, figi, isin, currency, logo_url, ticker.upper()))
        connect.commit()
    else:
        cursor.execute(
            "INSERT INTO bot_instruments (id, name, info, ticker, method, figi, isin, currency, logo_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (id, name, info, ticker.upper(), method, figi, isin, currency, logo_url))
        connect.commit()
    return get_instrument(ticker)


def update_database():
    c = 2841
    for i in ta_helper.get_all_events()[c:]:
        print(c, i)
        get_or_create_instrument(
            id=c,
            name=i['name'],
            info=get_info(i['ticker'], i['method']),
            ticker=i['ticker'],
            method=i['method'],
            figi=i['figi'],
            isin=i['isin'],
            currency=i['currency'],
            logo_url=get_logo(i['ticker'], i['method']),
        )
        c += 1


def sqlite_like(template_, value_):
    return sqlite_like_escape(template_, value_)


def sqlite_like_escape(template_, value_):
    re_ = re.compile(template_.lower().
                     replace(".", "\\.").replace("^", "\\^").replace("$", "\\$").
                     replace("*", "\\*").replace("+", "\\+").replace("?", "\\?").
                     replace("{", "\\{").replace("}", "\\}").replace("(", "\\(").
                     replace(")", "\\)").replace("[", "\\[").replace("]", "\\]").
                     replace("_", ".").replace("%", ".*?"))
    return re_.match(value_.lower()) is not None
    # Переопределение функции преобразования к нижнему регистру


def sqlite_lower(value_):
    return value_.lower()


# Переопределение правила сравнения строк
def sqlite_nocase_collation(value1_, value2_):
    return hash(value1_.lower()), hash(value2_.lower())


# Переопределение функции преобразования к верхнему геристру
def sqlite_upper(value_):
    return value_.upper()


connect.create_collation("BINARY", sqlite_nocase_collation)
connect.create_collation("NOCASE", sqlite_nocase_collation)
connect.create_function("LIKE", 2, sqlite_like)
connect.create_function("LOWER", 1, sqlite_lower)
connect.create_function("UPPER", 1, sqlite_upper)

if __name__ == '__main__':
    asyncio.run(main())
