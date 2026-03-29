from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(title="FastAPI Day 5 - Cart System", version="1.0.0")

# ─────────────────────────────────────────────
# Product catalogue (in-memory)
# ─────────────────────────────────────────────
products = [
    {"product_id": 1, "name": "Wireless Mouse", "price": 499, "in_stock": True,  "category": "Electronics"},
    {"product_id": 2, "name": "Notebook",        "price": 99,  "in_stock": True,  "category": "Stationery"},
    {"product_id": 3, "name": "USB Hub",          "price": 799, "in_stock": False, "category": "Electronics"},
    {"product_id": 4, "name": "Pen Set",          "price": 49,  "in_stock": True,  "category": "Stationery"},
]

# ─────────────────────────────────────────────
# In-memory cart and orders
# ─────────────────────────────────────────────
cart = []          # list of cart item dicts
orders = []        # list of placed order dicts
order_counter = 0  # auto-increment order_id


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────
def get_product(product_id: int):
    for p in products:
        if p["product_id"] == product_id:
            return p
    return None


# ─────────────────────────────────────────────
# Checkout request body schema
# ─────────────────────────────────────────────
class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str


# ─────────────────────────────────────────────
# Q1 / Q3 / Q4  — POST /cart/add
# Add a product to the cart.
# • If product not found → 404
# • If product out of stock → 400
# • If already in cart → update quantity ("Cart updated")
# • Otherwise → append new item ("Added to cart")
# ─────────────────────────────────────────────
@app.post("/cart/add")
def add_to_cart(product_id: int = Query(...), quantity: int = Query(1, ge=1)):
    product = get_product(product_id)

    # Q3 — 404 when product_id doesn't exist
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")

    # Q3 — 400 when product is out of stock
    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail=f"{product['name']} is out of stock")

    # Q4 — update quantity if product already in cart
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["subtotal"] = product["price"] * item["quantity"]
            return {"message": "Cart updated", "cart_item": item}

    # Q1 — add new item to cart
    cart_item = {
        "product_id":   product["product_id"],
        "product_name": product["name"],
        "quantity":     quantity,
        "unit_price":   product["price"],
        "subtotal":     product["price"] * quantity,
    }
    cart.append(cart_item)
    return {"message": "Added to cart", "cart_item": cart_item}


# ─────────────────────────────────────────────
# Q2  — GET /cart
# View the current cart with grand total.
# Returns a friendly message when cart is empty.
# ─────────────────────────────────────────────
@app.get("/cart")
def view_cart():
    if not cart:
        return {"message": "Cart is empty"}

    grand_total = sum(item["subtotal"] for item in cart)
    return {
        "items":       cart,
        "item_count":  len(cart),
        "grand_total": grand_total,
    }


# ─────────────────────────────────────────────
# Q5  — DELETE /cart/{product_id}
# Remove a product from the cart by product_id.
# Returns 404 if the product_id is not in the cart.
# ─────────────────────────────────────────────
@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):
    for i, item in enumerate(cart):
        if item["product_id"] == product_id:
            removed = cart.pop(i)
            return {"message": f"{removed['product_name']} removed from cart", "removed_item": removed}

    raise HTTPException(status_code=404, detail=f"Product id {product_id} is not in the cart")


# ─────────────────────────────────────────────
# Q5 / Q6 / Bonus — POST /cart/checkout
# Checkout: one order created per cart item.
# Bonus: returns 400 if cart is empty.
# Clears the cart after successful checkout.
# ─────────────────────────────────────────────
@app.post("/cart/checkout")
def checkout(request: CheckoutRequest):
    global order_counter

    # Bonus — reject empty cart with 400
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty — add items first")

    placed_orders = []
    for item in cart:
        order_counter += 1
        order = {
            "order_id":        order_counter,
            "customer_name":   request.customer_name,
            "delivery_address": request.delivery_address,
            "product":         item["product_name"],
            "quantity":        item["quantity"],
            "unit_price":      item["unit_price"],
            "total_price":     item["subtotal"],
        }
        orders.append(order)
        placed_orders.append(order)

    grand_total = sum(o["total_price"] for o in placed_orders)
    cart.clear()  # cart is emptied after checkout

    return {
        "message":      "Checkout successful",
        "customer_name": request.customer_name,
        "orders_placed": placed_orders,
        "grand_total":  grand_total,
    }


# ─────────────────────────────────────────────
# Q5 / Q6  — GET /orders
# List all orders placed so far.
# ─────────────────────────────────────────────
@app.get("/orders")
def get_orders():
    return {
        "orders":       orders,
        "total_orders": len(orders),
    }
