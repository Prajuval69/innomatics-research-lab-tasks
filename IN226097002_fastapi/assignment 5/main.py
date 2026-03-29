from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="FastAPI Day 6 - Search, Sort & Pagination", version="1.0.0")

# ─────────────────────────────────────────────
# In-memory data
# ─────────────────────────────────────────────
products = [
    {"product_id": 1, "name": "Wireless Mouse", "price": 499, "in_stock": True,  "category": "Electronics"},
    {"product_id": 2, "name": "Notebook",        "price": 99,  "in_stock": True,  "category": "Stationery"},
    {"product_id": 3, "name": "USB Hub",          "price": 799, "in_stock": False, "category": "Electronics"},
    {"product_id": 4, "name": "Pen Set",          "price": 49,  "in_stock": True,  "category": "Stationery"},
]

orders = []
order_counter = 0


# ─────────────────────────────────────────────
# Order request body
# ─────────────────────────────────────────────
class OrderRequest(BaseModel):
    customer_name: str
    product_id: int
    quantity: int = 1


# ─────────────────────────────────────────────
# POST /orders  — place an order
# (Needed so we have data for Q4 and Bonus)
# ─────────────────────────────────────────────
@app.post("/orders")
def place_order(req: OrderRequest):
    global order_counter

    product = next((p for p in products if p["product_id"] == req.product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail=f"{product['name']} is out of stock")

    order_counter += 1
    order = {
        "order_id":      order_counter,
        "customer_name": req.customer_name,
        "product":       product["name"],
        "quantity":      req.quantity,
        "unit_price":    product["price"],
        "total_price":   product["price"] * req.quantity,
    }
    orders.append(order)
    return {"message": "Order placed", "order": order}


# ─────────────────────────────────────────────
# GET /orders  — list all orders
# ─────────────────────────────────────────────
@app.get("/orders")
def get_orders():
    return {"orders": orders, "total_orders": len(orders)}


# ─────────────────────────────────────────────
# Q1  — GET /products/search
# Case-insensitive keyword search on product name.
# Returns friendly message when nothing matches.
# ─────────────────────────────────────────────
@app.get("/products/search")
def search_products(keyword: str = Query(...)):
    results = [p for p in products if keyword.lower() in p["name"].lower()]
    if not results:
        return {"message": f"No products found for: {keyword}", "total_found": 0, "products": []}
    return {"keyword": keyword, "total_found": len(results), "products": results}


# ─────────────────────────────────────────────
# Q2  — GET /products/sort
# Sort products by 'price' or 'name', asc or desc.
# Returns 400 for any other sort_by value.
# ─────────────────────────────────────────────
@app.get("/products/sort")
def sort_products(
    sort_by: str = Query("price"),
    order:   str = Query("asc"),
):
    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}

    reverse = order == "desc"
    sorted_products = sorted(products, key=lambda p: p[sort_by], reverse=reverse)
    return {
        "sort_by":  sort_by,
        "order":    order,
        "products": sorted_products,
        "total":    len(sorted_products),
    }


# ─────────────────────────────────────────────
# Q3  — GET /products/page
# Paginate the product list.
# ─────────────────────────────────────────────
@app.get("/products/page")
def get_products_paged(
    page:  int = Query(1, ge=1),
    limit: int = Query(2, ge=1, le=20),
):
    total = len(products)
    start = (page - 1) * limit
    paged = products[start: start + limit]
    total_pages = -(-total // limit)  # ceiling division

    return {
        "page":        page,
        "limit":       limit,
        "total":       total,
        "total_pages": total_pages,
        "products":    paged,
    }


# ─────────────────────────────────────────────
# Q4  — GET /orders/search
# Case-insensitive search on customer_name.
# ─────────────────────────────────────────────
@app.get("/orders/search")
def search_orders(customer_name: str = Query(...)):
    results = [
        o for o in orders
        if customer_name.lower() in o["customer_name"].lower()
    ]
    if not results:
        return {"message": f"No orders found for: {customer_name}"}
    return {"customer_name": customer_name, "total_found": len(results), "orders": results}


# ─────────────────────────────────────────────
# Q5  — GET /products/sort-by-category
# Sort by category (A→Z) first, then by price (asc).
# ─────────────────────────────────────────────
@app.get("/products/sort-by-category")
def sort_by_category():
    result = sorted(products, key=lambda p: (p["category"], p["price"]))
    return {"products": result, "total": len(result)}


# ─────────────────────────────────────────────
# Q6  — GET /products/browse
# Combined: filter by keyword → sort → paginate.
# All params are optional.
# ─────────────────────────────────────────────
@app.get("/products/browse")
def browse_products(
    keyword: Optional[str] = Query(None),
    sort_by: str           = Query("price"),
    order:   str           = Query("asc"),
    page:    int           = Query(1, ge=1),
    limit:   int           = Query(4, ge=1, le=20),
):
    # Step 1: Search / filter
    result = products
    if keyword:
        result = [p for p in result if keyword.lower() in p["name"].lower()]

    # Step 2: Sort
    if sort_by in ["price", "name"]:
        result = sorted(result, key=lambda p: p[sort_by], reverse=(order == "desc"))

    # Step 3: Paginate
    total       = len(result)
    start       = (page - 1) * limit
    paged       = result[start: start + limit]
    total_pages = -(-total // limit) if total > 0 else 0

    return {
        "keyword":     keyword,
        "sort_by":     sort_by,
        "order":       order,
        "page":        page,
        "limit":       limit,
        "total_found": total,
        "total_pages": total_pages,
        "products":    paged,
    }


# ─────────────────────────────────────────────
# Bonus  — GET /orders/page
# Paginate the orders list.
# ─────────────────────────────────────────────
@app.get("/orders/page")
def get_orders_paged(
    page:  int = Query(1, ge=1),
    limit: int = Query(3, ge=1, le=20),
):
    start = (page - 1) * limit
    return {
        "page":        page,
        "limit":       limit,
        "total":       len(orders),
        "total_pages": -(-len(orders) // limit) if orders else 0,
        "orders":      orders[start: start + limit],
    }


# ─────────────────────────────────────────────
# GET /products/{product_id}  — single product
# Must be placed AFTER all /products/... routes.
# ─────────────────────────────────────────────
@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = next((p for p in products if p["product_id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return product
