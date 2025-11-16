from sqlalchemy.orm import Session
from app.models.coupon import Coupon, get_ist_time
from app.models.schemas import (
    CouponCreate, CouponUpdate, Cart, ApplicableCoupon,
    UpdatedCart, UpdatedCartItem
)
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from fastapi import HTTPException
import pytz


class CouponService:
    """Service layer for coupon business logic"""

    @staticmethod
    def create_coupon(db: Session, coupon_data: CouponCreate) -> Coupon:
        """Create a new coupon"""
        try:
            # Check if code already exists
            existing = db.query(Coupon).filter(Coupon.code == coupon_data.code).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"Coupon code '{coupon_data.code}' already exists")
            
            # Extract repetition_limit from details only for BxGy coupons
            details = coupon_data.details.copy()
            repetition_limit = None
            
            if coupon_data.type == "bxgy":
                # Default to 1 if not provided for BxGy
                repetition_limit = details.pop('repition_limit', 1)
            
            # Set expiry to 1 day from now if not provided
            expires_at = coupon_data.expires_at
            if expires_at is None:
                expires_at = get_ist_time() + timedelta(days=1)
            
            coupon = Coupon(
                code=coupon_data.code,
                type=coupon_data.type,
                details=details,
                expires_at=expires_at,
                repetition_limit=repetition_limit
            )
            db.add(coupon)
            db.flush()  # Flush to get the ID without committing
            db.refresh(coupon)
            return coupon
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def get_all_coupons(db: Session) -> List[Coupon]:
        """Retrieve all coupons"""
        try:
            return db.query(Coupon).all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def get_coupon_by_id(db: Session, coupon_id: int) -> Optional[Coupon]:
        """Retrieve a specific coupon by ID"""
        try:
            return db.query(Coupon).filter(Coupon.id == coupon_id).first()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    @staticmethod
    def get_coupon_by_code(db: Session, code: str) -> Optional[Coupon]:
        """Retrieve a specific coupon by code (case-insensitive)"""
        try:
            return db.query(Coupon).filter(Coupon.code.ilike(code)).first()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def update_coupon(db: Session, coupon_id: int, coupon_data: CouponUpdate) -> Optional[Coupon]:
        """Update a specific coupon"""
        try:
            coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
            if not coupon:
                return None

            update_data = coupon_data.model_dump(exclude_unset=True)
            
            # Check if code is being updated and if it already exists
            if 'code' in update_data:
                existing = db.query(Coupon).filter(
                    Coupon.code == update_data['code'],
                    Coupon.id != coupon_id
                ).first()
                if existing:
                    raise HTTPException(status_code=400, detail=f"Coupon code '{update_data['code']}' already exists")
            
            # Extract repetition_limit from details only for BxGy coupons
            if 'details' in update_data and update_data['details']:
                details = update_data['details'].copy()
                
                # Only extract repition_limit if coupon type is bxgy
                if coupon.type == "bxgy":
                    # Default to 1 if not provided for BxGy
                    repetition_limit = details.pop('repition_limit', 1)
                    update_data['repetition_limit'] = repetition_limit
                else:
                    # For cart-wise and product-wise, ensure repetition_limit is None
                    update_data['repetition_limit'] = None
                
                update_data['details'] = details
            
            for field, value in update_data.items():
                setattr(coupon, field, value)

            coupon.updated_at = get_ist_time()
            db.flush()  # Flush changes without committing
            db.refresh(coupon)
            return coupon
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def delete_coupon(db: Session, coupon_id: int) -> bool:
        """Delete a specific coupon"""
        try:
            coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
            if not coupon:
                return False

            db.delete(coupon)
            db.flush()  # Flush deletion without committing
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def _is_coupon_valid(coupon: Coupon) -> bool:
        """Check if coupon is valid (active, not expired, usage limit not reached)"""
        if not coupon.is_active:
            return False

        if coupon.expires_at and coupon.expires_at < datetime.utcnow():
            return False

        if coupon.repetition_limit and coupon.times_used >= coupon.repetition_limit:
            return False

        return True

    @staticmethod
    def _calculate_cart_total(cart: Cart) -> float:
        """Calculate total cart value"""
        return sum(item.price * item.quantity for item in cart.items)

    @staticmethod
    def _calculate_cart_wise_discount(cart: Cart, details: Dict) -> float:
        """Calculate discount for cart-wise coupon"""
        threshold = details.get("threshold", 0)
        discount_percent = details.get("discount", 0)

        cart_total = CouponService._calculate_cart_total(cart)

        if cart_total >= threshold:
            return (cart_total * discount_percent) / 100
        return 0.0

    @staticmethod
    def _calculate_product_wise_discount(cart: Cart, details: Dict) -> float:
        """Calculate discount for product-wise coupon"""
        product_id = details.get("product_id")
        discount_percent = details.get("discount", 0)

        # Create cart lookup for O(1) access
        cart_map = {item.product_id: item for item in cart.items}
        
        if product_id in cart_map:
            item = cart_map[product_id]
            return (item.price * item.quantity * discount_percent) / 100
        
        return 0.0

    @staticmethod
    def _calculate_bxgy_discount(cart: Cart, details: Dict, repetition_limit: int = 1) -> float:
        """
        Calculate discount for BxGy coupon
        Buy products work with OR logic - any combination counts toward total sets
        Example: Buy 3 from [X,Y,Z] means 3X OR 3Y OR 3Z OR any combination
        """
        buy_products = details.get("buy_products", [])
        get_products = details.get("get_products", [])

        cart_map = {item.product_id: item for item in cart.items}

        # Calculate total sets available from all buy products (OR logic)
        total_buy_sets = 0
        for buy_prod in buy_products:
            prod_id = buy_prod.get("product_id")
            required_qty = buy_prod.get("quantity")
            
            if prod_id in cart_map:
                sets_from_this_product = cart_map[prod_id].quantity // required_qty
                total_buy_sets += sets_from_this_product
        
        if total_buy_sets == 0:
            return 0.0
        
        # Apply repetition limit
        applicable_times = min(total_buy_sets, repetition_limit)

        # Calculate discount for free products
        total_discount = 0.0
        for get_prod in get_products:
            prod_id = get_prod.get("product_id")
            free_qty_per_set = get_prod.get("quantity")
            
            if prod_id in cart_map:
                cart_item = cart_map[prod_id]
                total_free_qty = free_qty_per_set * applicable_times
                actual_free_qty = min(total_free_qty, cart_item.quantity)
                total_discount += cart_item.price * actual_free_qty

        return total_discount

    @staticmethod
    def get_applicable_coupons(db: Session, cart: Cart) -> List[ApplicableCoupon]:
        """Get all applicable coupons for a cart with calculated discounts"""
        try:
            coupons = db.query(Coupon).all()
            applicable = []

            for coupon in coupons:
                if not CouponService._is_coupon_valid(coupon):
                    continue

                discount = 0.0
                if coupon.type == "cart-wise":
                    discount = CouponService._calculate_cart_wise_discount(cart, coupon.details)
                elif coupon.type == "product-wise":
                    discount = CouponService._calculate_product_wise_discount(cart, coupon.details)
                elif coupon.type == "bxgy":
                    discount = CouponService._calculate_bxgy_discount(
                        cart, coupon.details, coupon.repetition_limit or 1
                    )

                if discount > 0:
                    applicable.append(ApplicableCoupon(
                        coupon_id=coupon.id,
                        type=coupon.type,
                        discount=round(discount, 2)
                    ))

            return applicable
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def apply_coupon(db: Session, coupon_id: int, cart: Cart) -> UpdatedCart:
        """Apply a specific coupon to cart and return updated cart"""
        try:
            coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
            
            if not coupon:
                raise HTTPException(status_code=404, detail="Coupon not found")

            if not CouponService._is_coupon_valid(coupon):
                raise HTTPException(status_code=400, detail="Coupon is not valid or has expired")
            
            # Increment usage counter
            coupon.times_used += 1
            db.flush()  # Flush changes without committing
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        # Calculate discount based on coupon type
        total_discount = 0.0
        updated_items = []

        if coupon.type == "cart-wise":
            total_discount = CouponService._calculate_cart_wise_discount(cart, coupon.details)
            
            if total_discount == 0:
                raise HTTPException(status_code=400, detail="Cart does not meet coupon conditions")
            
            # Distribute discount proportionally across items
            cart_total = CouponService._calculate_cart_total(cart)
            for item in cart.items:
                item_total = item.price * item.quantity
                item_discount = (item_total / cart_total) * total_discount
                updated_items.append(UpdatedCartItem(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.price,
                    total_discount=round(item_discount, 2)
                ))

        elif coupon.type == "product-wise":
            product_id = coupon.details.get("product_id")
            discount_percent = coupon.details.get("discount", 0)
            
            # Create cart lookup
            cart_map = {item.product_id: item for item in cart.items}
            
            if product_id not in cart_map:
                raise HTTPException(status_code=400, detail="Product not found in cart")
            
            for item in cart.items:
                item_discount = 0.0
                if item.product_id == product_id:
                    item_discount = (item.price * item.quantity * discount_percent) / 100
                    total_discount = item_discount
                
                updated_items.append(UpdatedCartItem(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.price,
                    total_discount=round(item_discount, 2)
                ))

        elif coupon.type == "bxgy":
            buy_products = coupon.details.get("buy_products", [])
            get_products = coupon.details.get("get_products", [])
            repetition_limit = coupon.repetition_limit or 1

            # Create cart lookup
            cart_map = {item.product_id: item for item in cart.items}

            # Calculate total sets available from all buy products (OR logic)
            total_buy_sets = 0
            for buy_prod in buy_products:
                prod_id = buy_prod.get("product_id")
                required_qty = buy_prod.get("quantity")
                
                if prod_id in cart_map:
                    sets_from_this_product = cart_map[prod_id].quantity // required_qty
                    total_buy_sets += sets_from_this_product

            if total_buy_sets == 0:
                raise HTTPException(status_code=400, detail="Buy products not found in cart")
            
            # Apply repetition limit
            applicable_times = min(total_buy_sets, repetition_limit)

            # Calculate free quantities for each get product
            free_quantities = {}
            for get_prod in get_products:
                prod_id = get_prod.get("product_id")
                free_qty_per_set = get_prod.get("quantity")
                total_free_qty = free_qty_per_set * applicable_times
                free_quantities[prod_id] = total_free_qty
            
            # Build updated items - add free quantities to existing cart items
            for item in cart.items:
                item_discount = 0.0
                item_quantity = item.quantity
                
                if item.product_id in free_quantities:
                    free_qty = free_quantities[item.product_id]
                    item_discount = item.price * free_qty
                    total_discount += item_discount
                    # Add free items to quantity
                    item_quantity += free_qty
                
                updated_items.append(UpdatedCartItem(
                    product_id=item.product_id,
                    quantity=item_quantity,
                    price=item.price,
                    total_discount=round(item_discount, 2)
                ))

        # Calculate totals
        # For BxGy, total_price includes free items
        if coupon.type == "bxgy":
            cart_total = sum(item.price * item.quantity for item in updated_items)
        else:
            cart_total = CouponService._calculate_cart_total(cart)
        
        final_price = cart_total - total_discount

        return UpdatedCart(
            items=updated_items,
            total_price=round(cart_total, 2),
            total_discount=round(total_discount, 2),
            final_price=round(final_price, 2)
        )
