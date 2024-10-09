import requests
import json
import logging
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URL API для цитат
API_URL = "https://quotes.toscrape.com/api/quotes?page={}"
AUTHOR_URL = "https://quotes.toscrape.com/author/{}"


# Асинхронная функция для получения данных с API
async def fetch_quotes_from_api(session, page_num):
    url = API_URL.format(page_num)
    try:
        async with session.get(url) as response:
            if response.status != 200:
                logging.error(f"Ошибка запроса: {url}, статус-код: {response.status}")
                return None
            return await response.json()
    except aiohttp.ClientError as e:
        logging.error(f"Ошибка при подключении к {url}: {e}")
        return None


# Функция для получения данных о рождении автора через пул потоков
def fetch_author_details_sync(author_slug):
    url = AUTHOR_URL.format(author_slug)
    try:
        response = requests.get(url)
        if response.status_code != 200:
            logging.error(f"Ошибка запроса автора: {url}, статус-код: {response.status_code}")
            return "Дата рождения неизвестна", "Место рождения неизвестно"
        soup = BeautifulSoup(response.text, 'lxml')
        born_date = soup.find('span', class_='author-born-date').text
        born_location = soup.find('span', class_='author-born-location').text
        return born_date, born_location
    except Exception as e:
        logging.error(f"Ошибка при парсинге данных автора: {e}")
        return "Дата рождения неизвестна", "Место рождения неизвестно"


# Асинхронная функция для получения всех цитат
async def scrape_all_quotes():
    page_number = 1
    all_quotes = []

    # Создаем сессию aiohttp для работы с API
    async with aiohttp.ClientSession() as session:
        while True:
            logging.info(f"Запрашиваем страницу: {page_number}")
            data = await fetch_quotes_from_api(session, page_number)

            if not data or 'quotes' not in data:
                break

            quotes = data['quotes']
            # Используем ThreadPoolExecutor для запросов к страницам авторов
            with ThreadPoolExecutor() as executor:
                loop = asyncio.get_event_loop()
                tasks = []

                for quote in quotes:
                    author_data = quote['author']

                    # Выполняем запрос к странице автора в пуле потоков
                    tasks.append(loop.run_in_executor(executor, fetch_author_details_sync, author_data['slug']))

                # Ждем выполнения всех запросов
                author_details = await asyncio.gather(*tasks)

                for i, quote in enumerate(quotes):
                    born_date, born_location = author_details[i]
                    quote_data = {
                        "author": {
                            "fullname": quote['author']['name'],
                            "born_date": born_date,
                            "born_location": born_location,
                        },
                        "quote": quote['text'],
                        "tags": quote['tags']
                    }
                    all_quotes.append(quote_data)

            # Проверяем, есть ли следующая страница
            if not data['has_next']:
                logging.info("Все страницы были обработаны.")
                break

            page_number += 1

    return all_quotes


# Функция для сохранения данных в JSON
def save_to_json(data, filename="quotes.json"):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Данные успешно сохранены в файл {filename}")
    except IOError as e:
        logging.error(f"Ошибка при записи данных в файл {filename}: {e}")


# Асинхронная главная функция
async def main():
    all_quotes = await scrape_all_quotes()
    save_to_json(all_quotes)


# Запуск асинхронной программы
if __name__ == "__main__":
    asyncio.run(main())
