# Coupon Management API

RESTful API for managing and applying discount coupons (cart-wise, product-wise, BxGy) for e-commerce platforms.

## Quick Start

```bash
# 1. Install dependencies
uv sync

# Or with test dependencies
uv sync --extra test

# 2. Set up PostgreSQL database (choose one method)
# Method A: Using SQL script (creates database + tables + sample data)
psql -U postgres -f app/scripts/setup_database.sql

# Method B: Manual
psql -U postgres -c "CREATE DATABASE coupons_db;"
uv run python setup_db.py

# 3. Configure database connection
# Create .env file with your PostgreSQL credentials:
# DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/coupons_db

# 4. Run server
uv run python main.py

OR 

uvicorn main:app --reload

# 5. Access API docs
# http://localhost:8000/docs
```

## Tech Stack

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/coupons` | Create coupon |
| GET | `/api/coupons` | Get all coupons |
| GET | `/api/coupons/{id}` | Get coupon by ID |
| GET | `/api/coupons/code/{code}` | Get coupon by code |
| GET | `/api/coupons/{id}/stats` | Get coupon usage statistics |
| PUT | `/api/coupons/{id}` | Update coupon |
| DELETE | `/api/coupons/{id}` | Delete coupon |
| POST | `/api/applicable-coupons` | Get applicable coupons for cart |
| POST | `/api/apply-coupon/{id}` | Apply coupon by ID |


## Use Cases

### Implemented Cases ✅

**Cart-wise:**
- Percentage discount with minimum threshold
- Proportional discount distribution across items
- Threshold validation
- Discount applies to entire cart value

**Product-wise:**
- Product-specific percentage discount
- Applies to all quantities of the product
- Product existence validation
- Discount calculated per product

**BxGy:**
- Flexible buy/get product arrays (OR logic - any combination counts)
- Repetition limit support (extracted from details and stored separately)
- Partial fulfillment handling (gives free items up to available quantity)
- Minimum quantity validation
- Multiple buy products can contribute to same offer
- Calculates total sets from all qualifying products

**General:**
- Coupon expiration dates (auto-set to 1 day if not provided)
- Usage tracking with `times_used` counter
- Repetition limits (max times coupon can be used)
- Active/inactive status toggle
- Comprehensive error handling
- Alphanumeric coupon codes (case-insensitive lookup)
- IST timezone for all timestamps
- Usage statistics endpoint
- Automatic usage counter increment on application

### Unimplemented Cases (Documented) 📝

**Cart-wise:** Tiered discounts, fixed amount discounts, max discount caps, minimum item count, category-based, time restrictions, user segments, shipping thresholds, minimum/maximum cart value ranges

**Product-wise:** Multiple products in single coupon, quantity-based tiers, fixed amounts, category-wide, brand-specific, variant-specific, max quantity limits, exclude sale items, bundle discounts

**BxGy:** AND logic for buy products (must buy all specified), same-product BxGy (buy X get more of same free), tiered BxGy (different tiers), percentage discount instead of free, cheapest item free, category-based, mix and match, progressive discounts, minimum value requirements, cross-category offers

**General:** Stackable coupons, priority rules, user-specific tracking, purchase history requirements, geographic restrictions, payment method restrictions, analytics dashboard, referral coupons, loyalty points integration, auto-apply best coupon, coupon notifications

**Edge Cases:** Negative prices prevention, floating point precision, concurrent usage control, partial returns handling, currency conversion, tax calculation, inventory validation, cart modifications during checkout, fraud detection, fractional quantities, race conditions on usage limits

## Limitations

1. **Single coupon application** - Only one coupon can be applied per transaction
2. **No authentication** - Since this is only meant for coupon management microservice, auth can be added in future extension
3. **No user tracking** - Coupons not tied to specific users or user sessions
4. **No inventory validation** - Doesn't check stock availability for free products in BxGy
5. **No transaction history** - Doesn't persist applied coupons to orders (requires order management integration)
6. **No taxing system** - Discounts calculated on pre-tax amounts; GST services can be added as future extension
7. **Percentage discounts only** - No fixed amount discounts (e.g., flat $20 off)
8. **Simple BxGy logic** - Uses OR logic for buy products; doesn't support AND conditions
9. **No category support** - Products identified only by ID, no category/brand grouping
10. **No concurrent control** - No distributed locking for usage limits in high-traffic scenarios
11. **No audit trail** - Doesn't log detailed coupon usage history per application
12. **No rate limiting** - API endpoints not protected against abuse
13. **Case-insensitive codes** - Coupon codes are case-insensitive (SAVE10 = save10)
14. **Auto-expiry only** - Default 1-day expiry; no support for "valid until used" coupons

## Assumptions

1. **Product IDs are valid** - All product IDs in coupons and carts exist in the product catalog
2. **Single currency** - All prices are in the same currency (no multi-currency support)
3. **Positive values** - Prices and quantities are always positive numbers
4. **Valid cart structure** - Cart data is well-formed and contains valid items
5. **Pre-tax discounts** - Discounts calculated on pre-tax amounts; tax applied after discount
6. **No inventory check** - Free products (BxGy) are assumed to be in stock
7. **IST timezone** - All timestamps use Indian Standard Time (Asia/Kolkata)
8. **Decimal precision** - All monetary values rounded to 2 decimal places
9. **Auto-expiry** - Coupons expire 1 day from creation unless explicitly set
10. **Immediate application** - Coupons applied instantly; no delayed processing
11. **OR logic for BxGy** - Multiple buy products use OR condition (any combination works)
12. **Proportional cart discount** - Cart-wise discounts distributed proportionally across items
13. **Usage counter manual** - `times_used` incremented on application, not on order completion
14. **Repetition limit extraction** - BxGy `repition_limit` extracted from details and stored separately
15. **Case-insensitive lookup** - Coupon code search is case-insensitive
16. **No partial discounts** - Either full discount applies or none (no partial threshold discounts)
17. **Stateless API** - Each request is independent; no session management
18. **Synchronous processing** - All operations are synchronous; no async/background jobs


## Testing

```bash
# Install with test dependencies
uv sync --extra test

# Run tests
uv run pytest app/test/ -v

# Run with coverage
uv run pytest app/test/ --cov=app --cov-report=html
```

## Project Structure

```
coupon-management/
├── app/
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py              # PostgreSQL configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── coupon.py                # SQLAlchemy models
│   │   └── schemas.py               # Pydantic schemas
│   ├── router/
│   │   ├── __init__.py
│   │   └── coupon_router.py         # API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── coupon_service.py        # Business logic
│   ├── scripts/
│   │   ├── setup_database.sql       # Database setup script
│   │   └── Coupon Mgmt.postman_collection.json  # Postman collection
│   └── test/
│       ├── __init__.py
│       └── test_coupon_service.py   # Unit tests
├── .env                              # Environment variables (not in git)
├── .env.example                      # Environment template
├── .gitignore                        # Git ignore rules
├── main.py                           # Application entry point
├── pyproject.toml                    # Dependencies & config
├── README.md                         # This file
└── uv.lock                           # Dependency lock file
```

## Error Handling

- **404** - Coupon not found
- **400** - Cart doesn't meet coupon conditions
- **422** - Invalid input data (validation errors)

## Future Enhancements

1. Authentication for Coupon Management
2. Stackable coupons with priority rules
3. Fixed amount discounts
4. Tiered discount levels
5. Category-based coupons
6. User-specific coupons
7. Analytics dashboard
8. Coupon usage history


