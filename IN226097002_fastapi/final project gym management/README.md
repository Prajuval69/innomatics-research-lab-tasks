# 💪 IronFit Gym Management System — FastAPI

A complete **Gym Management System** backend built with **FastAPI**, implementing all 20 questions from the internship project (Day 1 → Day 6).

---

## 🚀 How to Run

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/fastapi-gym-management-system.git
cd fastapi-gym-management-system

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
uvicorn main:app --reload

# 4. Open Swagger UI
# http://127.0.0.1:8000/docs
```

---

## 📋 All 20 Questions — Endpoints

| Q# | Method | Endpoint | Description | Day |
|----|--------|----------|-------------|-----|
| Q1  | GET    | `/`                                        | Welcome to IronFit Gym                    | Day 1 |
| Q2  | GET    | `/plans`                                   | All plans + total, min_price, max_price   | Day 1 |
| Q3  | GET    | `/plans/{plan_id}`                         | Get plan by ID or 404                     | Day 1 |
| Q4  | GET    | `/memberships`                             | All memberships + total                   | Day 1 |
| Q5  | GET    | `/plans/summary`                           | Stats: totals, cheapest, most expensive   | Day 1 |
| Q6  | POST   | `/memberships`                             | Pydantic: phone min_length=10 enforced    | Day 2 |
| Q7  | —      | Helper functions                           | `find_plan()`, `calculate_membership_fee()` | Day 3 |
| Q8  | POST   | `/memberships`                             | Enroll with fee, discounts, status        | Day 2+3 |
| Q9  | POST   | `/memberships`                             | Referral code: extra 5% off + breakdown   | Day 2+3 |
| Q10 | GET    | `/plans/filter`                            | Filter by max_price, duration, classes, trainer | Day 3 |
| Q11 | POST   | `/plans`                                   | Create plan, reject duplicate names (201) | Day 4 |
| Q12 | PUT    | `/plans/{plan_id}`                         | Update price/classes/trainer via query    | Day 4 |
| Q13 | DELETE | `/plans/{plan_id}`                         | Delete plan; block if active members      | Day 4 |
| Q14 | POST   | `/classes/book`                            | Book class (must have active + classes plan) | Day 5 |
| Q14 | GET    | `/classes/bookings`                        | List all class bookings                   | Day 5 |
| Q15 | DELETE | `/classes/cancel/{booking_id}`             | Cancel a class booking                    | Day 5 |
| Q15 | PUT    | `/memberships/{membership_id}/freeze`      | Freeze (pause) membership                 | Day 5 |
| Q15 | PUT    | `/memberships/{membership_id}/reactivate`  | Reactivate frozen membership              | Day 5 |
| Q16 | GET    | `/plans/search?keyword=`                   | Keyword search; 'classes'/'trainer' special | Day 6 |
| Q17 | GET    | `/plans/sort`                              | Sort by price/name/duration_months        | Day 6 |
| Q18 | GET    | `/plans/page`                              | Paginate plans (page + limit)             | Day 6 |
| Q19 | GET    | `/memberships/search`                      | Search memberships by member_name         | Day 6 |
| Q19 | GET    | `/memberships/sort`                        | Sort by total_fee or duration_months      | Day 6 |
| Q19 | GET    | `/memberships/page`                        | Paginate memberships                      | Day 6 |
| Q20 | GET    | `/plans/browse`                            | Combined: keyword→filter→sort→paginate    | Day 6+3 |

---

## 🧠 Concepts Implemented

### Day 1 – GET APIs
- `GET /` home route, `GET /plans` list, `GET /plans/{id}` by ID, `GET /plans/summary` stats

### Day 2 – POST + Pydantic Validation
- `EnrollRequest` with `min_length`, `gt`, `default`, pattern constraints
- Phone with `min_length=10` → 5-digit phone returns **HTTP 422**

### Day 3 – Helper Functions
- `find_plan(plan_id)` — lookup helper
- `calculate_membership_fee()` — 10%/20% duration discounts, 5% referral, ₹200 EMI fee
- `filter_plans_logic()` — `is not None` checks for optional filters
- `GET /plans/filter` with optional `Query()` params

### Day 4 – CRUD Operations
- `POST /plans` → 201 Created, duplicate name check
- `PUT /plans/{plan_id}` → partial update via query params, 404 if missing
- `DELETE /plans/{plan_id}` → 404 if missing, error if active memberships exist

### Day 5 – Multi-Step Workflows
- **Class Workflow**: Book → List → Cancel
- **Membership Lifecycle**: Enroll → Freeze → Reactivate

### Day 6 – Advanced APIs
- Keyword search (`/plans/search`) with special keywords: `classes`, `trainer`
- Sorting (`/plans/sort`, `/memberships/sort`) with validation
- Pagination (`/plans/page`, `/memberships/page`) with `total_pages`
- Combined browse (`/plans/browse`): keyword → filter → sort → paginate

---

## ⚠️ Route Order Rule Applied
All fixed routes (`/plans/summary`, `/plans/filter`, `/plans/search`, etc.) are declared **before** the variable route `/plans/{plan_id}` to avoid routing conflicts.

---

## 📦 Tech Stack
- **FastAPI** — Modern Python web framework
- **Pydantic v2** — Data validation & constraints
- **Uvicorn** — ASGI server
- **Swagger UI** — Auto-generated at `/docs`

---

## 📸 Screenshots
All 20 Swagger screenshots are in the `screenshots/` folder:
`Q1_home.png` → `Q20_combined_browse.png`

---

*Built as part of the FastAPI Internship at Innomatics Research Labs* 🚀
