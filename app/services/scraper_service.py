import re
import requests
from bs4 import BeautifulSoup

from app.services.exchange_service import get_exchange_rate_gbp_to_sek

BASE_URL = "http://books.toscrape.com/"

"""
this function scrapes all the categories in the website provided
"""
def scrape_all_categories() -> list[dict]:
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    categories = []
    category_section = soup.find("ul", class_="nav nav-list")

    for link in category_section.find_all("a"):
        name = link.text.strip()
        url = BASE_URL + link["href"]

        if name.lower() != "books":
            categories.append({"name": name, "url": url})

    return categories

"""
this function gets all the books in a spesific category
"""
def scrape_books_from_category(category_url: str) -> list[dict]:
    books = []
    exchange_rate = get_exchange_rate_gbp_to_sek()
    page_url = category_url
    book_id = 1

    while True:
        response = requests.get(page_url)
        soup = BeautifulSoup(response.text, "html.parser")

        for article in soup.find_all("article", class_="product_pod"):
            title = article.h3.a["title"]
            price_gbp = float(re.sub(r"[^\d.]", "", article.find("p", class_="price_color").text))
            price_sek = round(price_gbp * exchange_rate, 2)
            rating = article.find("p", class_="star-rating")["class"][1]

            books.append({
                "id": book_id,
                "title": title,
                "price_gbp": price_gbp,
                "price_sek": price_sek,
                "rating": rating
            })
            book_id += 1

        next_button = soup.find("li", class_="next")
        if next_button:
            next_page = next_button.a["href"]
            if "catalogue/" in page_url:
                page_url = page_url.rsplit("/", 1)[0] + "/" + next_page
            else:
                page_url = category_url.replace("index.html", next_page)
        else:
            break

    return books