"""
Rutas SEO: sitemap.xml dinámico y robots.txt
"""
from datetime import date
from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter(tags=["seo"])

BASE_URL = "https://heydemin.com"


@router.get("/robots.txt", include_in_schema=False)
def robots_txt():
    content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /docs
Disallow: /redoc

Sitemap: {BASE_URL}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap_xml():
    today = date.today().isoformat()

    static_urls = [
        {"loc": f"{BASE_URL}/",         "priority": "1.0", "changefreq": "daily"},
        {"loc": f"{BASE_URL}/#catalog", "priority": "0.9", "changefreq": "daily"},
        {"loc": f"{BASE_URL}/#about",   "priority": "0.6", "changefreq": "monthly"},
        {"loc": f"{BASE_URL}/#reviews", "priority": "0.5", "changefreq": "weekly"},
    ]

    urls_xml = ""
    for u in static_urls:
        urls_xml += f"""
  <url>
    <loc>{u['loc']}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{u['changefreq']}</changefreq>
    <priority>{u['priority']}</priority>
  </url>"""

    return Response(
        content=f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls_xml}
</urlset>""",
        media_type="application/xml",
    )
