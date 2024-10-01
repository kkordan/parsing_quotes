import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def parse_quote_page(session, page_num):
    url = f"https://quotes.toscrape.com/page/{page_num}"
    page_content = await fetch(session, url)
    soup = BeautifulSoup(page_content, 'lxml')

    quotes = soup.find_all('span', class_='text')
    authors = soup.find_all('small', class_='author')
    tags = soup.find_all('div', class_='tags')
    quote_spans = soup.find_all('div', class_='quote')

    href_values = []
    for quote in quote_spans:
        spans = quote.find_all('span', class_=False)
        for span in spans:
            a_tag = span.find('a', href=True)
            if a_tag:
                href_values.append(a_tag['href'])

    results = []
    for ii in range(len(quotes)):

        author_url = f"https://quotes.toscrape.com{href_values[ii]}"
        author_page = await fetch(session, author_url)
        soup_2 = BeautifulSoup(author_page, 'lxml')

        author_born_date = soup_2.find('span', class_='author-born-date').text
        author_born_location = soup_2.find('span', class_='author-born-location').text

        tagsforquote = tags[ii].find_all('a', class_='tag')
        tag_list = [tagforquote.text for tagforquote in tagsforquote]

        quote_data = {
            "author": {
                "fullname": authors[ii].text,
                "born_date": author_born_date,
                "born_location": author_born_location,
            },
            "quote": quotes[ii].text,
            "tags": tag_list
        }
        results.append(quote_data)

    return results


async def main():
    quotes_data = []

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(1, 11):
            tasks.append(parse_quote_page(session, i))

        all_quotes = await asyncio.gather(*tasks)

        for quotes_page in all_quotes:
            quotes_data.extend(quotes_page)

    with open('quotes1.json', 'w', encoding='utf-8') as json_file:
        json.dump(quotes_data, json_file, ensure_ascii=False, indent=4)


asyncio.run(main())
