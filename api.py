import aiohttp
import asyncio

base_url = 'http://localhost:8000'


async def create_user(external_id, name):
    url = f'{base_url}/users/create/'
    data = {'external_id': external_id, 'name': name}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            try:
                response.raise_for_status()
                json_data = await response.json()
                return json_data
            except (aiohttp.ClientResponseError, aiohttp.ContentTypeError) as e:
                print(f'Error during create_user request: {e}')
                return None


async def get_user(external_id):
    url = f'{base_url}/users/get/?query={external_id}'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            try:
                response.raise_for_status()
                json_data = await response.json()
                return json_data
            except (aiohttp.ClientResponseError, aiohttp.ContentTypeError) as e:
                print(f'Error during get_user request: {e}')
                return None


async def delete_user(external_id):
    url = f'{base_url}/users/delete/?external_id={external_id}'

    async with aiohttp.ClientSession() as session:
        async with session.delete(url) as response:
            try:
                response.raise_for_status()
                return True
            except aiohttp.ClientResponseError as e:
                print(f'Error during delete_user request: {e}')
                return False


async def get_all_users():
    url = f'{base_url}/users/all/'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                json_data = await response.json()
                return json_data
            else:
                return {'error': 'Failed to get all users.'}


async def search_instrument(query):
    url = f'{base_url}/instruments/search/?query={query}'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            try:
                response.raise_for_status()
                json_data = await response.json()
                return json_data
            except (aiohttp.ClientResponseError, aiohttp.ContentTypeError) as e:
                print(f'Error during search_instrument request: {e}')
                return None


async def get_instrument(ticker):
    url = f'{base_url}/instruments/get/?query={ticker}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            try:
                response.raise_for_status()
                json_data = await response.json()
                return json_data
            except (aiohttp.ClientResponseError, aiohttp.ContentTypeError) as e:
                print(f'Error during get_instrument request: {e}')
                return None


async def get_all_instruments():
    url = f'{base_url}/instruments/all/'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                json_data = await response.json()
                return json_data
            else:
                return {'error': 'Failed to get all instruments.'}


async def main():
    # Удаление пользователя
    create_user_result = await create_user('1', 'Tom')
    print(create_user_result)

    # Получение пользователя
    get_user_result = await get_user('1')
    print(get_user_result)

    # Удаление пользователя
    delete_user_result = await delete_user('1')
    print(delete_user_result)

    a = await get_instrument('LKOH')
    print(a)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
