from flask import Blueprint, request, render_template
from content.blog_promo import BlogPromoContent
import content.blog_promo.sitemaps as sitemaps

blog_promo_bp = Blueprint('blog_promo', __name__, url_prefix='/blog_promo')

@blog_promo_bp.route("/post_blog_promo", methods=["POST"])
def post_blog_promo():  
    b = BlogPromoContent()
    d = b.post_blog_promo()
    if d:
        return d.result()
    else:
        return "No content", 204

@blog_promo_bp.route("/update_sitemap", methods=["POST"])
def update_sitemap():
    # sitemap_url = request.json["sitemap_url"]
    sitemap_url = "https://meyerperin.org/sitemap.xml"
    sitemaps.process_sitemap(sitemap_url)

    return "OK", 200
