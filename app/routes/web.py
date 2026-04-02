import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

# ✅ Ruta ABSOLUTA al directorio /app/app/templates (robusto en Railway/Linux)
BASE_DIR = Path(__file__).resolve().parent.parent  # .../app/app
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

PRODUCTS_PATH = BASE_DIR / "data" / "products.json"
CARS_PATH = BASE_DIR / "data" / "cars.json"


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_products() -> List[Dict[str, Any]]:
    data = load_json(PRODUCTS_PATH)
    if not data:
        return []
    if isinstance(data, dict) and "products" in data:
        return data["products"]
    if isinstance(data, list):
        return data
    return []


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


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    products = load_products()
    featured = products[:6]
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "featured": featured,
            "page_title": "Car3D Files — Archivos 3D para autos",
        },
    )


@router.get("/catalog", response_class=HTMLResponse)
def catalog(request: Request, q: str = "", category: str = "all"):
    products = load_products()
    categories = unique_categories(products)
    filtered = [p for p in products if product_matches(p, q=q, category=category)]

    return templates.TemplateResponse(
        "catalog.html",
        {
            "request": request,
            "products": filtered,
            "q": q,
            "category": category,
            "categories": categories,
            "page_title": "Catálogo — Car3D Files",
        },
    )


@router.get("/p/{slug}", response_class=HTMLResponse)
def product_detail(request: Request, slug: str):
    products = load_products()
    product = find_by_slug(products, slug)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # ✅ Compatibilidad: algunos templates usan `product`, otros usan `p`
    return templates.TemplateResponse(
        "product.html",
        {
            "request": request,
            "product": product,
            "p": product,
            "page_title": f"{product.get('name', 'Producto')} — Car3D Files",
        },
    )


@router.get("/autos", response_class=HTMLResponse)
def autos(request: Request):
    cars = load_cars()
    return templates.TemplateResponse(
        "autos.html",
        {
            "request": request,
            "cars": cars,
            "page_title": "Autos — Car3D Files",
        },
    )


@router.get("/faq", response_class=HTMLResponse)
def faq(request: Request):
    return templates.TemplateResponse(
        "faq.html",
        {"request": request, "page_title": "FAQ — Car3D Files"},
    )


@router.get("/legal", response_class=HTMLResponse)
def legal(request: Request):
    return templates.TemplateResponse(
        "legal.html",
        {"request": request, "page_title": "Legal — Car3D Files"},
    )