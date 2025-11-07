import aiohttp
from ..config import API_BASE

async def api_login(username, password):
    url = f"{API_BASE}/token"
    data = {'username': username, 'password': password}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    async with aiohttp.ClientSession() as s:
        async with s.post(url, data=data, headers=headers) as resp:
            return resp.status, await resp.json() if resp.content_type == 'application/json' else await resp.text()

async def api_get_cards(token: str):
    url = f"{API_BASE}/cards"
    headers = {'Authorization': f'Bearer {token}'}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers) as resp:
            return resp.status, await resp.json() if resp.content_type == 'application/json' else await resp.text()

async def api_add_card(token: str, payload: dict):
    url = f"{API_BASE}/cards"
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=payload, headers=headers) as resp:
            return resp.status, await resp.json() if resp.content_type == 'application/json' else await resp.text()

async def api_get_subs(token: str):
    url = f"{API_BASE}/subscriptions"
    headers = {'Authorization': f'Bearer {token}'}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers) as resp:
            return resp.status, await resp.json() if resp.content_type == 'application/json' else await resp.text()

async def api_add_sub(token: str, payload: dict):
    url = f"{API_BASE}/subscriptions"
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=payload, headers=headers) as resp:
            return resp.status, await resp.json() if resp.content_type == 'application/json' else await resp.text()

async def api_del_sub(token: str, sub_id: int):
    url = f"{API_BASE}/subscriptions/{sub_id}"
    headers = {'Authorization': f'Bearer {token}'}
    async with aiohttp.ClientSession() as s:
        async with s.delete(url, headers=headers) as resp:
            return resp.status, await resp.json() if resp.content_type == 'application/json' else await resp.text()

# ... (существующие функции)

async def api_get_cards_id(token: str, card_id: int):
    """Получает RAW данные карты по ID."""
    url = f"{API_BASE}/cards/{card_id}"
    headers = {'Authorization': f'Bearer {token}'}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers) as resp:
            return resp.status, await resp.json() if resp.content_type == 'application/json' else await resp.text()

# Добавьте также для подписок, чтобы не было ошибок
async def api_get_subs_id(token: str, sub_id: int):
    """Получает данные подписки по ID."""
    url = f"{API_BASE}/subscriptions/{sub_id}"
    headers = {'Authorization': f'Bearer {token}'}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers) as resp:
            return resp.status, await resp.json() if resp.content_type == 'application/json' else await resp.text()