from flask import Blueprint, jsonify

from app.repositories import category_repository
from app.services import scraper_service

categories_bp = Blueprint("categories", __name__, url_prefix="/api/v1/categories")

"""
this route scrapes the wnire website for all different sorts of categories
"""
@categories_bp.route("/", methods=["GET"])
def fetch_categories():
    categories = scraper_service.scrape_all_categories()
    category_repository.save_all(categories)
    return jsonify(categories)


"""
here we get the URL of a category that has already been scraped
"""
@categories_bp.route("/<category_name>", methods=["GET"])
def get_category(category_name):
    url = category_repository.get_url_by_name(category_name)

    if not url:
        return jsonify({"error": "Category not found"}), 404

    return jsonify({"category": category_name, "url": url})