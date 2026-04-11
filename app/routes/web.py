import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

# Ruta absoluta robusta (Railway/Linux)
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

PRODUCTS_PATH = BASE_DIR / "data" / "products.json"
CARS_PATH = BASE_DIR / "data" / "cars.json"

PLACEHOLDER_IMAGE_PATHS = {
    "/static/img/hero.jpg",
    "/static/img/hero.jpeg",
    "/static/img/hero.png",
}

PLACEHOLDER_URL_MARKERS = (
    "XXXXXX",
    "placeholder",
    "example.com",
)


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def is_public_url(url: Any) -> bool:
    if not isinstance(url, str):
        return False

    value = url.strip()
    if not value:
        return False

    value_lower = value.lower()
    return not any(marker.lower() in value_lower for marker in PLACEHOLDER_URL_MARKERS)


def sanitize_product(product: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(product)

    images = item.get("images") or []
    first_image = images[0].strip() if images and isinstance(images[0], str) else ""
    item["has_home_image"] = bool(first_image) and first_image not in PLACEHOLDER_IMAGE_PATHS

    if not is_public_url(item.get("hotmart_url")):
        item["hotmart_url"] = ""

    if not is_public_url(item.get("digital_checkout_url")):
        item["digital_checkout_url"] = ""

    if not is_public_url(item.get("printed_request_url")):
        item["printed_request_url"] = ""

    return item


def load_products() -> List[Dict[str, Any]]:
    data = load_json(PRODUCTS_PATH)
    if not data:
        return []

    if isinstance(data, dict) and "products" in data:
        products = data["products"]
    elif isinstance(data, list):
        products = data
    else:
        return []

    return [sanitize_product(p) for p in products]


def load_cars() -> List[Dict[str, Any]]:
    data = load_json(CARS_PATH)
    if not data:
        return []
    if isinstance(data, dict) and "cars" in data:
        return data["cars"]
    if isinstance(data, list):
        return data
    return []


def find_by_slug(items: List[Dict[str, Any]], slug: str) -> Optional[Dict[str, Any]]:
    for it in items:
        if it.get("slug") == slug:
            return it
    return None


def normalize(s: str) -> str:
    return (s or "").strip().lower()


def product_matches(p: Dict[str, Any], q: str, category: str) -> bool:
    qn = normalize(q)
    cn = normalize(category)

    if cn and cn != "all" and normalize(p.get("category", "")) != cn:
        return False

    if not qn:
        return True

    haystack_parts = [
        p.get("name", ""),
        p.get("short_desc", ""),
        p.get("long_desc", ""),
        p.get("category", ""),
        " ".join(p.get("tags", []) or []),
    ]
    haystack = normalize(" ".join(haystack_parts))
    return qn in haystack


def unique_categories(products: List[Dict[str, Any]]) -> List[str]:
    cats: List[str] = []
    seen = set()
    for p in products:
        c = (p.get("category") or "").strip()
        if c and c.lower() not in seen:
            seen.add(c.lower())
            cats.append(c)
    return cats


def render_html(template_name: str, request: Request, **ctx) -> HTMLResponse:
    """
    Render robusto para Railway/Python 3.13.
    Evita el bug de TemplateResponse y devuelve HTMLResponse.
    """
    template = templates.env.get_template(template_name)
    html = template.render(request=request, **ctx)
    return HTMLResponse(html)


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    products = load_products()
    featured = [p for p in products if p.get("has_home_image")][:6]

    return render_html(
        "home.html",
        request,
        featured=featured,
        page_title="Car3D Files — Archivos 3D para autos",
    )


@router.get("/catalog", response_class=HTMLResponse)
def catalog(request: Request, q: str = "", category: str = "all"):
    products = load_products()
    categories = unique_categories(products)
    filtered = [p for p in products if product_matches(p, q=q, category=category)]

    return render_html(
        "catalog.html",
        request,
        products=filtered,
        q=q,
        category=category,
        categories=categories,
        page_title="Catálogo — Car3D Files",
    )


@router.get("/p/{slug}", response_class=HTMLResponse)
def product_detail(request: Request, slug: str):
    products = load_products()
    product = find_by_slug(products, slug)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return render_html(
        "product.html",
        request,
        product=product,
        p=product,
        page_title=f"{product.get('name', 'Producto')} — Car3D Files",
    )


@router.get("/autos", response_class=HTMLResponse)
def autos(request: Request):
    cars = load_cars()
    return render_html(
        "autos.html",
        request,
        cars=cars,
        page_title="Autos — Car3D Files",
    )


@router.get("/faq", response_class=HTMLResponse)
def faq(request: Request):
    return render_html(
        "faq.html",
        request,
        page_title="FAQ — Car3D Files",
    )


@router.get("/legal", response_class=HTMLResponse)
def legal(request: Request):
    return render_html(
        "legal.html",
        request,
        page_title="Legal — Car3D Files",
    )