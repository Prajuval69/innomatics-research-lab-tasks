from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="Product Inventory API")

# ── INITIAL DATA ──
products = [
    {"id": 1, "name": "Wireless Mouse", "category": "Electronics", "price": 29, "in_stock": True},
    {"id": 2, "name": "USB-C Cable", "category": "Electronics", "price": 15, "in_stock": True},
    {"id": 3, "name": "USB Hub", "category": "Electronics", "price": 799, "in_stock": False},
    {"id": 4, "name": "Pen Set", "category": "Stationery", "price": 12, "in_stock": True},
]

# ── PYDANTIC MODEL ──
class Product(BaseModel):
    name: str
    category: str
    price: int
    in_stock: bool


# ──────────────────────────────────────────────────────────────────
# ── Q1: POST /products — Create a new product with duplicate check ──
# ──────────────────────────────────────────────────────────────────
@app.post("/products", status_code=201)
def create_product(product: Product):
    """
    Create a new product.
    Returns 400 if a product with the same name already exists.
    """
    # Check for duplicate product name
    if any(p["name"].lower() == product.name.lower() for p in products):
        raise HTTPException(
            status_code=400,
            detail=f"Product '{product.name}' already exists"
        )
    
    # Generate new ID
    new_id = max((p["id"] for p in products), default=0) + 1
    
    new_product = {
        "id": new_id,
        "name": product.name,
        "category": product.category,
        "price": product.price,
        "in_stock": product.in_stock,
    }
    
    products.append(new_product)
    
    return {
        "id": new_id,
        "message": f"Product '{product.name}' created successfully",
        "product": new_product
    }


# ──────────────────────────────────────────────────────────────────
# ── Q2: PUT /products/{product_id} — Update product fields ──
# ──────────────────────────────────────────────────────────────────
@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    in_stock: Optional[bool] = Query(None, description="Update stock status"),
    price: Optional[int] = Query(None, description="Update price"),
):
    """
    Update a product's in_stock and/or price fields.
    At least one field must be provided.
    Returns 404 if product not found.
    """
    # Find the product
    product = next((p for p in products if p["id"] == product_id), None)
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Track what was updated
    updated_fields = {}
    
    if in_stock is not None:
        product["in_stock"] = in_stock
        updated_fields["in_stock"] = in_stock
    
    if price is not None:
        product["price"] = price
        updated_fields["price"] = price
    
    if not updated_fields:
        raise HTTPException(
            status_code=400,
            detail="At least one field (in_stock or price) must be provided"
        )
    
    return {
        "id": product_id,
        "message": f"Product '{product['name']}' updated successfully",
        "updated_fields": updated_fields,
        "product": product
    }


# ──────────────────────────────────────────────────────────────────
# ── Q3: DELETE /products/{product_id} — Remove a product ──
# ──────────────────────────────────────────────────────────────────
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    """
    Delete a product by ID.
    Returns 404 if product not found.
    """
    # Find and remove the product
    global products
    product = next((p for p in products if p["id"] == product_id), None)
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found"
        )
    
    product_name = product["name"]
    products = [p for p in products if p["id"] != product_id]
    
    return {
        "message": f"Product '{product_name}' deleted successfully",
        "deleted_id": product_id
    }


# ──────────────────────────────────────────────────────────────────
# ── Q5: GET /products/audit — Inventory statistics ──
# ── (Place ABOVE /products/{product_id} so it matches first) ──
# ──────────────────────────────────────────────────────────────────
@app.get("/products/audit")
def product_audit():
    """
    Get comprehensive inventory audit:
    - Total number of products
    - Count of in-stock products
    - List of out-of-stock product names
    - Total stock value (price × 10 units per product)
    - Most expensive product
    """
    in_stock_list = [p for p in products if p["in_stock"]]
    out_stock_list = [p for p in products if not p["in_stock"]]
    stock_value = sum(p["price"] * 10 for p in in_stock_list)
    priciest = max(products, key=lambda p: p["price"]) if products else None
    
    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock_list),
        "out_of_stock_names": [p["name"] for p in out_stock_list],
        "total_stock_value": stock_value,
        "most_expensive": {"name": priciest["name"], "price": priciest["price"]} if priciest else None,
    }


# ──────────────────────────────────────────────────────────────────
# ── BONUS: PUT /products/discount — Category-wide discount ──
# ── (Place ABOVE /products/{product_id}) ──
# ──────────────────────────────────────────────────────────────────
@app.put("/products/discount")
def bulk_discount(
    category: str = Query(..., description="Category to discount"),
    discount_percent: int = Query(..., ge=1, le=99, description="% off"),
):
    """
    Apply a discount to all products in a specific category.
    """
    updated = []
    for p in products:
        if p["category"] == category:
            p["price"] = int(p["price"] * (1 - discount_percent / 100))
            updated.append(p)
    
    if not updated:
        return {
            "message": f"No products found in category: {category}"
        }
    
    return {
        "message": f"{discount_percent}% discount applied to {category}",
        "updated_count": len(updated),
        "updated_products": updated,
    }


# ──────────────────────────────────────────────────────────────────
# ── Q4: GET /products — Fetch all products (for CRUD lifecycle) ──
# ──────────────────────────────────────────────────────────────────
@app.get("/products")
def get_all_products():
    """
    Retrieve all products (unordered).
    """
    return {
        "count": len(products),
        "products": products
    }


# ──────────────────────────────────────────────────────────────────
# ── GET /products/{product_id} — Fetch a single product ──
# ──────────────────────────────────────────────────────────────────
@app.get("/products/{product_id}")
def get_product(product_id: int):
    """
    Retrieve a single product by ID.
    Returns 404 if not found.
    """
    product = next((p for p in products if p["id"] == product_id), None)
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found"
        )
    
    return product


# ──────────────────────────────────────────────────────────────────
# ── Root endpoint (for testing) ──
# ──────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Welcome to Product Inventory API. Use /docs for interactive documentation."}
