import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re

BASE_URL = "http://books.toscrape.com/"

def get_all_categories():
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    categories = []

    category_section = soup.find("ul", class_="nav nav-list")
    links = category_section.find_all("a")

    for link in links:
        name = link.text.strip()
        url = BASE_URL + link["href"]

        # Hoppa över "Books" (huvudkategorin)
        if name.lower() != "books":
            categories.append({
                "name": name,
                "url": url
            })

    return categories

def save_categories_to_json(categories):
    if not os.path.exists("data"):
        os.makedirs("data")

    with open("data/categories.json", "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=4, ensure_ascii=False)

def get_today_filename(category_name):
    today = datetime.now().strftime("%y%m%d")
    filename = f"data/{category_name.lower()}_{today}.json"
    return filename

def get_or_create_books(category_name, category_url):
    if not os.path.exists("data"):
        os.makedirs("data")

    filename = get_today_filename(category_name)

    # Om fil redan finns → använd den
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    # Annars → webscrapa och skapa ny fil
    books = scrape_books_from_category(category_url)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(books, f, indent=4, ensure_ascii=False)

    return books

def get_category_url_from_json(category_name):
    file_path = "data/categories.json"

    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        categories = json.load(f)

    for category in categories:
        if category["name"].lower() == category_name.lower():
            return category["url"]

    return None

def scrape_books_from_category(category_url):
    books = []
    exchange_rate = get_exchange_rate_gbp_to_sek()
    page_url = category_url
    book_id = 1

    while True:
        response = requests.get(page_url)
        soup = BeautifulSoup(response.text, "html.parser")

        articles = soup.find_all("article", class_="product_pod")

        for article in articles:
            title = article.h3.a["title"]

            raw_price = article.find("p", class_="price_color").text
            cleaned_price = re.sub(r"[^\d.]", "", raw_price)
            price_gbp = float(cleaned_price)
            price_sek = round(price_gbp * exchange_rate, 2)

            rating_class = article.find("p", class_="star-rating")["class"]
            rating = rating_class[1]

            book = {
                "id": book_id,
                "title": title,
                "price_gbp": price_gbp,
                "price_sek": price_sek,
                "rating": rating
            }

            books.append(book)
            book_id += 1

        # Kolla om det finns nästa sida
        next_button = soup.find("li", class_="next")

        if next_button:
            next_page = next_button.a["href"]

            # Bygg korrekt nästa URL
            if "catalogue/" in page_url:
                base = page_url.rsplit("/", 1)[0]
                page_url = base + "/" + next_page
            else:
                page_url = category_url.replace("index.html", next_page)
        else:
            break

    return books

def get_exchange_rate_gbp_to_sek():
    url = "https://www.x-rates.com/calculator/?from=GBP&to=SEK&amount=1"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Växelkursen ligger i span med class ccOutputRslt
    result = soup.find("span", class_="ccOutputRslt").text
    
    # Exempeltext: "13.52 SEK"
    rate = result.split(" ")[0]

    return float(rate)

def add_book_to_category(category_name, new_book_data):
    filename = get_today_filename(category_name)

    # Om filen inte finns → skapa den via scraping
    if not os.path.exists(filename):
        category_url = get_category_url_from_json(category_name)
        if not category_url:
            return {"error": "Category not found"}

        books = scrape_books_from_category(category_url)
    else:
        with open(filename, "r", encoding="utf-8") as f:
            books = json.load(f)

    # Skapa nytt unikt ID
    if books:
        new_id = max(book["id"] for book in books) + 1
    else:
        new_id = 1

    new_book = {
        "id": new_id,
        "title": new_book_data.get("title"),
        "price_gbp": new_book_data.get("price_gbp"),
        "price_sek": new_book_data.get("price_sek"),
        "rating": new_book_data.get("rating")
    }

    books.append(new_book)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(books, f, indent=4, ensure_ascii=False)

    return new_book

def update_book_in_category(category_name, book_id, updated_data):
    filename = get_today_filename(category_name)

    if not os.path.exists(filename):
        return {"error": "Category file not found"}

    with open(filename, "r", encoding="utf-8") as f:
        books = json.load(f)

    for book in books:
        if book["id"] == book_id:
            book.update(updated_data)

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(books, f, indent=4, ensure_ascii=False)

            return book

    return {"error": "Book not found"}

def delete_book_from_category(category_name, book_id):
    filename = get_today_filename(category_name)

    if not os.path.exists(filename):
        return {"error": "Category file not found"}

    with open(filename, "r", encoding="utf-8") as f:
        books = json.load(f)

    updated_books = [book for book in books if book["id"] != book_id]

    if len(updated_books) == len(books):
        return {"error": "Book not found"}

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(updated_books, f, indent=4, ensure_ascii=False)

    return {"message": "Book deleted successfully"}