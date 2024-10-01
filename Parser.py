import requests
from bs4 import BeautifulSoup
import json

quotes_data = []

for i in range(1, 2):
    url = f"https://quotes.toscrape.com/page/{i}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

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


    for ii in range(0, len(quotes)):

        url_2 = f"https://quotes.toscrape.com{href_values[ii]}"
        response_2 = requests.get(url_2)
        soup_2 = BeautifulSoup(response_2.text, 'lxml')


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


        quotes_data.append(quote_data)

with open('quotes.json', 'w', encoding='utf-8') as json_file:
    json.dump(quotes_data, json_file, ensure_ascii=False, indent=4)


