from flask import Flask, jsonify, request
from scraper import get_all_categories, save_categories_to_json, get_category_url_from_json, get_or_create_books, add_book_to_category, update_book_in_category, delete_book_from_category

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "Web Scraping API is running!"})

@app.route("/api/v1/categories", methods=["GET"])
def fetch_categories():
    categories = get_all_categories()
    save_categories_to_json(categories)
    return jsonify(categories)

@app.route("/api/v1/categories/<category_name>", methods=["GET"])
def get_category_url(category_name):
    url = get_category_url_from_json(category_name)

    if url:
        return jsonify({
            "category": category_name,
            "url": url
        })
    else:
        return jsonify({"error": "Category not found"}), 404

@app.route("/api/v1/books/<category_name>", methods=["GET"])
def get_books_by_category(category_name):
    category_url = get_category_url_from_json(category_name)

    if not category_url:
        return jsonify({"error": "Category not found"}), 404

    books = get_or_create_books(category_name, category_url)
    return jsonify(books)

@app.route("/api/v1/books/<category_name>", methods=["POST"])
def add_book(category_name):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    result = add_book_to_category(category_name, data)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result), 201

@app.route("/api/v1/books/<category_name>/<int:book_id>", methods=["PUT"])
def update_book(category_name, book_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    result = update_book_in_category(category_name, book_id, data)

    if "error" in result:
        return jsonify(result), 404

    return jsonify(result)

@app.route("/api/v1/books/<category_name>/<int:book_id>", methods=["DELETE"])
def delete_book(category_name, book_id):
    result = delete_book_from_category(category_name, book_id)

    if "error" in result:
        return jsonify(result), 404

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)


