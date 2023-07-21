import sqlite3
import json
import asyncio

connect = sqlite3.connect('db.sqlite3', check_same_thread=False)
cursor = connect.cursor()


def inst_serializer(instrument):
    names = [column[0] for column in cursor.description]
    serialized_instruments = [{names[i]: row[i] for i in range(len(row))} for row in instrument]
    return serialized_instruments[0]


async def user_serializer(user):
    fields = ['external_id', 'name']
    serialized_users = [{fields[i]: row[i] for i in range(len(row))} for row in user]
    return serialized_users[0]


async def get_all_users():
    rows = cursor.execute("SELECT * FROM bot_users;").fetchall()
    users = [{'name': row[0], 'external_id': row[1]} for row in rows]
    return users


async def create_user(external_id, username):
    cursor.execute(f"INSERT INTO bot_users VALUES (:name, :external_id);",
                   {'name': username, 'external_id': external_id})
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


async def search_instrument(ticker):
    rows = cursor.execute(f"SELECT * FROM bot_instruments WHERE ticker=?", (ticker,)).fetchall()
    instrument = [{'ticker': row[0], 'name': row[1]} for row in rows]
    return instrument


async def get_instrument(ticker):
    return inst_serializer(cursor.execute(f"SELECT * FROM bot_instruments WHERE ticker=?", (ticker.upper(),)).fetchall())


async def main():
    print("TEST db_helper.py")
    await create_user(123456, 'Tom')
    users = await get_all_users()
    print(json.dumps(users))  # Вывод пользователей в формате JSON
    user = await get_user(123456)
    print(json.dumps(user))  # Вывод пользователя в формате JSON
    await delete_user(123456)
    user = await get_user(123456)
    print(json.dumps(user))  # Вывод пользователя в формате JSON
    inst = await get_instrument('moex')
    print(inst)


if __name__ == '__main__':
    asyncio.run(main())
