# /quesecrides/middleware/seo_index_middleware.py

from django.utils.deprecation import MiddlewareMixin

ALLOWED_VIEW_NAMES = {
    "home",
    "shop-page",
    "category-parent",
    "category-child",
    "product-detail",
    "product-detail-child",
    "blog:list",
    "blog:category",
    "blog:detail",
}

class SEOIndexControlMiddleware(MiddlewareMixin):
    """
    Sirf selected views ko index allow karta hai.
    Baaki sab pe 'X-Robots-Tag: noindex, nofollow' lagata hai.
    HTML responses par hi apply hota hai (text/html).
    """

    def process_response(self, request, response):
        # Content-Type check: sirf HTML par header lagao
        content_type = response.headers.get("Content-Type", "") or response.get("Content-Type", "")
        is_html = content_type.startswith("text/html")

        if not is_html:
            return response

        # resolver_match se current matched view ka name nikal lo
        resolver_match = getattr(request, "resolver_match", None)
        view_name = resolver_match.view_name if resolver_match else None

        if view_name in ALLOWED_VIEW_NAMES:
            # Allowed pages -> index, follow
            response.headers["X-Robots-Tag"] = "index, follow"
        else:
            # Sab kuch aur -> noindex, nofollow
            response.headers["X-Robots-Tag"] = "noindex, nofollow"

        return response
