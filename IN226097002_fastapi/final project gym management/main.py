from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(
    title="IronFit Gym Management System",
    description="Complete Gym Management API — Q1 to Q20",
    version="1.0.0"
)

# ─────────────────────────────────────────────────────────────
# In-Memory Data Stores
# ─────────────────────────────────────────────────────────────

plans = [
    {"id": 1, "name": "Basic",    "duration_months": 1,  "price": 500,  "includes_classes": False, "includes_trainer": False},
    {"id": 2, "name": "Standard", "duration_months": 3,  "price": 1200, "includes_classes": True,  "includes_trainer": False},
    {"id": 3, "name": "Premium",  "duration_months": 6,  "price": 2000, "includes_classes": True,  "includes_trainer": False},
    {"id": 4, "name": "Elite",    "duration_months": 12, "price": 3500, "includes_classes": True,  "includes_trainer": True},
    {"id": 5, "name": "Trial",    "duration_months": 1,  "price": 300,  "includes_classes": False, "includes_trainer": False},
]
plan_counter = 6

memberships = []
membership_counter = 1

class_bookings = []
class_counter = 1


# ─────────────────────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────────────────────

class EnrollRequest(BaseModel):
    member_name:   str = Field(..., min_length=2,  example="Aarav Sharma")
    plan_id:       int = Field(..., gt=0,           example=3)
    phone:         str = Field(..., min_length=10,  example="9876543210")
    start_month:   str = Field(..., min_length=3,   example="July")
    payment_mode:  str = Field(default="cash",      example="cash")
    referral_code: str = Field(default="",          example="REF123")

class NewPlan(BaseModel):
    name:             str  = Field(..., min_length=2, example="Diamond")
    duration_months:  int  = Field(..., gt=0,         example=6)
    price:            int  = Field(..., gt=0,         example=2500)
    includes_classes: bool = Field(default=False)
    includes_trainer: bool = Field(default=False)

class ClassBookRequest(BaseModel):
    member_name: str = Field(..., example="Aarav Sharma")
    class_name:  str = Field(..., example="Zumba")
    class_date:  str = Field(..., example="2024-08-10")


# ─────────────────────────────────────────────────────────────
# Helper Functions  (Day 3)
# ─────────────────────────────────────────────────────────────

def find_plan(plan_id: int):
    return next((p for p in plans if p["id"] == plan_id), None)

def calculate_membership_fee(base_price: int, duration_months: int,
                              payment_mode: str, referral_code: str = "") -> dict:
    discount_pct = 0
    discount_label = "No discount"

    if duration_months >= 12:
        discount_pct = 20
        discount_label = "20% discount (12+ months)"
    elif duration_months >= 6:
        discount_pct = 10
        discount_label = "10% discount (6+ months)"

    after_duration = base_price * (1 - discount_pct / 100)

    referral_discount = 0.0
    if referral_code.strip() != "":
        referral_discount = after_duration * 0.05
        after_duration -= referral_discount

    processing_fee = 200 if payment_mode == "emi" else 0
    total_fee = after_duration + processing_fee

    return {
        "base_price":        base_price,
        "duration_discount": f"{discount_pct}%",
        "discount_label":    discount_label,
        "referral_discount": round(referral_discount, 2),
        "processing_fee":    processing_fee,
        "total_fee":         round(total_fee, 2),
    }

def filter_plans_logic(max_price=None, max_duration=None,
                        includes_classes=None, includes_trainer=None):
    result = plans[:]
    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]
    if max_duration is not None:
        result = [p for p in result if p["duration_months"] <= max_duration]
    if includes_classes is not None:
        result = [p for p in result if p["includes_classes"] == includes_classes]
    if includes_trainer is not None:
        result = [p for p in result if p["includes_trainer"] == includes_trainer]
    return result


# ─────────────────────────────────────────────────────────────
# ROUTE ORDER: fixed routes BEFORE variable /plans/{plan_id}
# ─────────────────────────────────────────────────────────────

# Q1 — GET /
@app.get("/", tags=["General"])
def home():
    """Q1 — Welcome route"""
    return {"message": "Welcome to IronFit Gym"}


# Q2 — GET /plans
@app.get("/plans", tags=["Plans"])
def get_all_plans():
    """Q2 — All plans with total, min_price, max_price"""
    prices = [p["price"] for p in plans]
    return {
        "total":     len(plans),
        "min_price": min(prices),
        "max_price": max(prices),
        "plans":     plans,
    }


# Q5 — GET /plans/summary  (fixed — must be above /plans/{plan_id})
@app.get("/plans/summary", tags=["Plans"])
def plans_summary():
    """Q5 — Total, classes count, trainer count, cheapest, most expensive"""
    with_classes   = [p for p in plans if p["includes_classes"]]
    with_trainer   = [p for p in plans if p["includes_trainer"]]
    cheapest       = min(plans, key=lambda p: p["price"])
    most_expensive = max(plans, key=lambda p: p["price"])
    return {
        "total_plans":         len(plans),
        "plans_with_classes":  len(with_classes),
        "plans_with_trainer":  len(with_trainer),
        "cheapest_plan":       {"name": cheapest["name"],       "price": cheapest["price"]},
        "most_expensive_plan": {"name": most_expensive["name"], "price": most_expensive["price"]},
    }


# Q10 — GET /plans/filter
@app.get("/plans/filter", tags=["Plans"])
def filter_plans(
    max_price:        Optional[int]  = Query(None),
    max_duration:     Optional[int]  = Query(None),
    includes_classes: Optional[bool] = Query(None),
    includes_trainer: Optional[bool] = Query(None),
):
    """Q10 — Filter plans with optional query params"""
    result = filter_plans_logic(max_price, max_duration, includes_classes, includes_trainer)
    if not result:
        raise HTTPException(status_code=404, detail="No plans match the given filters.")
    return {"total_found": len(result), "plans": result}


# Q16 — GET /plans/search
@app.get("/plans/search", tags=["Plans"])
def search_plans(keyword: str = Query(...)):
    """Q16 — Keyword search; special: 'classes' or 'trainer'"""
    kw = keyword.lower()
    if kw == "classes":
        result = [p for p in plans if p["includes_classes"]]
    elif kw == "trainer":
        result = [p for p in plans if p["includes_trainer"]]
    else:
        result = [p for p in plans if kw in p["name"].lower()]
    return {"keyword": keyword, "total_found": len(result), "plans": result}


# Q17 — GET /plans/sort
@app.get("/plans/sort", tags=["Plans"])
def sort_plans(
    sort_by: str = Query("price", description="price | name | duration_months"),
    order:   str = Query("asc",   description="asc | desc"),
):
    """Q17 — Sort plans"""
    valid = ["price", "name", "duration_months"]
    if sort_by not in valid:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {valid}")
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="order must be 'asc' or 'desc'")
    sorted_plans = sorted(plans, key=lambda p: p[sort_by], reverse=(order == "desc"))
    return {"sort_by": sort_by, "order": order, "plans": sorted_plans}


# Q18 — GET /plans/page
@app.get("/plans/page", tags=["Plans"])
def paginate_plans(
    page:  int = Query(1, ge=1),
    limit: int = Query(2, ge=1),
):
    """Q18 — Paginate plans"""
    total       = len(plans)
    total_pages = max(1, (total + limit - 1) // limit)
    if page > total_pages:
        raise HTTPException(status_code=404, detail=f"Page {page} exceeds total pages ({total_pages}).")
    start  = (page - 1) * limit
    result = plans[start: start + limit]
    return {"page": page, "limit": limit, "total": total, "total_pages": total_pages, "plans": result}


# Q20 — GET /plans/browse
@app.get("/plans/browse", tags=["Plans"])
def browse_plans(
    keyword:          Optional[str]  = Query(None),
    includes_classes: Optional[bool] = Query(None),
    includes_trainer: Optional[bool] = Query(None),
    sort_by:          str            = Query("price"),
    order:            str            = Query("asc"),
    page:             int            = Query(1, ge=1),
    limit:            int            = Query(2, ge=1),
):
    """Q20 — Combined: keyword → filters → sort → paginate"""
    result = plans[:]
    if keyword is not None:
        kw = keyword.lower()
        if kw == "classes":
            result = [p for p in result if p["includes_classes"]]
        elif kw == "trainer":
            result = [p for p in result if p["includes_trainer"]]
        else:
            result = [p for p in result if kw in p["name"].lower()]
    if includes_classes is not None:
        result = [p for p in result if p["includes_classes"] == includes_classes]
    if includes_trainer is not None:
        result = [p for p in result if p["includes_trainer"] == includes_trainer]
    valid = ["price", "name", "duration_months"]
    if sort_by in valid:
        result = sorted(result, key=lambda p: p[sort_by], reverse=(order == "desc"))
    total       = len(result)
    total_pages = max(1, (total + limit - 1) // limit)
    start       = (page - 1) * limit
    paginated   = result[start: start + limit]
    return {
        "metadata": {
            "keyword": keyword, "includes_classes": includes_classes,
            "includes_trainer": includes_trainer, "sort_by": sort_by,
            "order": order, "page": page, "limit": limit,
            "total_results": total, "total_pages": total_pages,
        },
        "plans": paginated,
    }


# Q3 — GET /plans/{plan_id}  (variable — MUST be after all fixed /plans/* routes)
@app.get("/plans/{plan_id}", tags=["Plans"])
def get_plan_by_id(plan_id: int):
    """Q3 — Get a single plan by ID"""
    plan = find_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan with ID {plan_id} not found.")
    return plan


# Q11 — POST /plans
@app.post("/plans", tags=["Plans"], status_code=201)
def create_plan(new_plan: NewPlan):
    """Q11 — Create plan; reject duplicate names"""
    global plan_counter
    if any(p["name"].lower() == new_plan.name.lower() for p in plans):
        raise HTTPException(status_code=400, detail=f"A plan named '{new_plan.name}' already exists.")
    plan = {
        "id": plan_counter, "name": new_plan.name,
        "duration_months": new_plan.duration_months, "price": new_plan.price,
        "includes_classes": new_plan.includes_classes, "includes_trainer": new_plan.includes_trainer,
    }
    plans.append(plan)
    plan_counter += 1
    return {"message": "Plan created successfully!", "plan": plan}


# Q12 — PUT /plans/{plan_id}
@app.put("/plans/{plan_id}", tags=["Plans"])
def update_plan(
    plan_id:          int,
    price:            Optional[int]  = Query(None),
    includes_classes: Optional[bool] = Query(None),
    includes_trainer: Optional[bool] = Query(None),
):
    """Q12 — Update plan fields via optional query params"""
    plan = find_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")
    if price            is not None: plan["price"]            = price
    if includes_classes is not None: plan["includes_classes"] = includes_classes
    if includes_trainer is not None: plan["includes_trainer"] = includes_trainer
    return {"message": "Plan updated successfully!", "plan": plan}


# Q13 — DELETE /plans/{plan_id}
@app.delete("/plans/{plan_id}", tags=["Plans"])
def delete_plan(plan_id: int):
    """Q13 — Delete plan; block if active memberships exist"""
    plan = find_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")
    active = [m for m in memberships if m["plan_id"] == plan_id and m["status"] == "active"]
    if active:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete '{plan['name']}': {len(active)} active membership(s) exist."
        )
    plans.remove(plan)
    return {"message": f"Plan '{plan['name']}' deleted successfully."}


# ─────────────────────────────────────────────────────────────
# MEMBERSHIPS
# ─────────────────────────────────────────────────────────────

# Q19a — GET /memberships/search  (fixed — above variable routes)
@app.get("/memberships/search", tags=["Memberships"])
def search_memberships(member_name: str = Query(...)):
    """Q19 — Search memberships by member name"""
    kw     = member_name.lower()
    result = [m for m in memberships if kw in m["member_name"].lower()]
    return {"total_found": len(result), "memberships": result}


# Q19b — GET /memberships/sort
@app.get("/memberships/sort", tags=["Memberships"])
def sort_memberships(
    sort_by: str = Query("total_fee", description="total_fee | duration_months"),
    order:   str = Query("asc"),
):
    """Q19 — Sort memberships"""
    valid = ["total_fee", "duration_months"]
    if sort_by not in valid:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {valid}")
    sorted_m = sorted(memberships, key=lambda m: m[sort_by], reverse=(order == "desc"))
    return {"sort_by": sort_by, "order": order, "memberships": sorted_m}


# Q19c — GET /memberships/page
@app.get("/memberships/page", tags=["Memberships"])
def paginate_memberships(
    page:  int = Query(1, ge=1),
    limit: int = Query(2, ge=1),
):
    """Q19 — Paginate memberships"""
    total       = len(memberships)
    total_pages = max(1, (total + limit - 1) // limit)
    start       = (page - 1) * limit
    return {
        "page": page, "limit": limit,
        "total": total, "total_pages": total_pages,
        "memberships": memberships[start: start + limit],
    }


# Q4 — GET /memberships
@app.get("/memberships", tags=["Memberships"])
def get_all_memberships():
    """Q4 — Return all memberships and total"""
    return {"total": len(memberships), "memberships": memberships}


# Q8 + Q9 — POST /memberships
@app.post("/memberships", tags=["Memberships"], status_code=201)
def enroll_member(request: EnrollRequest):
    """Q8/Q9 — Enroll member with fee calculation, discounts, referral"""
    global membership_counter
    plan = find_plan(request.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan ID {request.plan_id} not found.")

    fee_details = calculate_membership_fee(
        plan["price"], plan["duration_months"],
        request.payment_mode, request.referral_code,
    )
    monthly_equivalent = round(fee_details["total_fee"] / plan["duration_months"], 2)

    membership = {
        "membership_id":      membership_counter,
        "member_name":        request.member_name,
        "phone":              request.phone,
        "plan_id":            plan["id"],
        "plan_name":          plan["name"],
        "duration_months":    plan["duration_months"],
        "start_month":        request.start_month,
        "payment_mode":       request.payment_mode,
        "referral_code":      request.referral_code,
        "monthly_equivalent": monthly_equivalent,
        "fee_breakdown":      fee_details,
        "total_fee":          fee_details["total_fee"],
        "status":             "active",
        "includes_classes":   plan["includes_classes"],
        "includes_trainer":   plan["includes_trainer"],
    }
    memberships.append(membership)
    membership_counter += 1
    return {"message": "Membership enrolled successfully!", "membership": membership}


# Q15b — PUT /memberships/{membership_id}/freeze
@app.put("/memberships/{membership_id}/freeze", tags=["Memberships"])
def freeze_membership(membership_id: int):
    """Q15 — Freeze (pause) a membership"""
    m = next((m for m in memberships if m["membership_id"] == membership_id), None)
    if not m:
        raise HTTPException(status_code=404, detail=f"Membership {membership_id} not found.")
    if m["status"] == "frozen":
        raise HTTPException(status_code=400, detail="Membership is already frozen.")
    m["status"] = "frozen"
    return {"message": "Membership frozen.", "membership": m}


# Q15c — PUT /memberships/{membership_id}/reactivate
@app.put("/memberships/{membership_id}/reactivate", tags=["Memberships"])
def reactivate_membership(membership_id: int):
    """Q15 — Reactivate a frozen membership"""
    m = next((m for m in memberships if m["membership_id"] == membership_id), None)
    if not m:
        raise HTTPException(status_code=404, detail=f"Membership {membership_id} not found.")
    if m["status"] == "active":
        raise HTTPException(status_code=400, detail="Membership is already active.")
    m["status"] = "active"
    return {"message": "Membership reactivated.", "membership": m}


# ─────────────────────────────────────────────────────────────
# CLASS BOOKINGS  (Day 5)
# ─────────────────────────────────────────────────────────────

# Q14a — POST /classes/book
@app.post("/classes/book", tags=["Classes"], status_code=201)
def book_class(request: ClassBookRequest):
    """Q14 — Book class; member must have active membership with classes"""
    global class_counter
    active_membership = next(
        (m for m in memberships
         if m["member_name"].lower() == request.member_name.lower()
         and m["status"] == "active"
         and m["includes_classes"]),
        None,
    )
    if not active_membership:
        raise HTTPException(
            status_code=403,
            detail=f"'{request.member_name}' does not have an active membership that includes classes.",
        )
    booking = {
        "booking_id":    class_counter,
        "member_name":   request.member_name,
        "class_name":    request.class_name,
        "class_date":    request.class_date,
        "membership_id": active_membership["membership_id"],
        "status":        "booked",
    }
    class_bookings.append(booking)
    class_counter += 1
    return {"message": "Class booked successfully!", "booking": booking}


# Q14b — GET /classes/bookings
@app.get("/classes/bookings", tags=["Classes"])
def get_class_bookings():
    """Q14 — List all class bookings"""
    return {"total": len(class_bookings), "bookings": class_bookings}


# Q15a — DELETE /classes/cancel/{booking_id}
@app.delete("/classes/cancel/{booking_id}", tags=["Classes"])
def cancel_class(booking_id: int):
    """Q15 — Cancel a class booking"""
    booking = next((b for b in class_bookings if b["booking_id"] == booking_id), None)
    if not booking:
        raise HTTPException(status_code=404, detail=f"Booking ID {booking_id} not found.")
    class_bookings.remove(booking)
    return {"message": f"Class booking {booking_id} cancelled successfully."}

# ─────────────────────────────────────────────────────────────
# Q6 note: EnrollRequest enforces phone min_length=10 via Pydantic.
# Sending a 5-digit phone automatically returns HTTP 422 Unprocessable Entity.
# ─────────────────────────────────────────────────────────────
