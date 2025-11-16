from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models.schemas import (
    CouponCreate, CouponUpdate, CouponResponse,
    ApplicableCouponsRequest, ApplicableCouponsResponse,
    ApplyCouponRequest, ApplyCouponResponse
)
from app.services import CouponService

router = APIRouter(prefix="/api", tags=["coupons"])


@router.post("/coupons", response_model=CouponResponse, status_code=201)
def create_coupon(coupon: CouponCreate, db: Session = Depends(get_db)):
    """Create a new coupon"""
    return CouponService.create_coupon(db, coupon)


@router.get("/coupons", response_model=List[CouponResponse])
def get_all_coupons(db: Session = Depends(get_db)):
    """Retrieve all coupons"""
    return CouponService.get_all_coupons(db)


@router.get("/coupons/{id}", response_model=CouponResponse)
def get_coupon(id: int, db: Session = Depends(get_db)):
    """Retrieve a specific coupon by ID"""
    coupon = CouponService.get_coupon_by_id(db, id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return coupon


@router.get("/coupons/code/{code}", response_model=CouponResponse)
def get_coupon_by_code(code: str, db: Session = Depends(get_db)):
    """Retrieve a specific coupon by code"""
    coupon = CouponService.get_coupon_by_code(db, code)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return coupon


@router.put("/coupons/{id}", response_model=CouponResponse)
def update_coupon(id: int, coupon: CouponUpdate, db: Session = Depends(get_db)):
    """Update a specific coupon by ID"""
    updated_coupon = CouponService.update_coupon(db, id, coupon)
    if not updated_coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return updated_coupon


@router.delete("/coupons/{id}", status_code=204)
def delete_coupon(id: int, db: Session = Depends(get_db)):
    """Delete a specific coupon by ID"""
    success = CouponService.delete_coupon(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return None


@router.post("/applicable-coupons", response_model=ApplicableCouponsResponse)
def get_applicable_coupons(request: ApplicableCouponsRequest, db: Session = Depends(get_db)):
    """Fetch all applicable coupons for a given cart"""
    applicable = CouponService.get_applicable_coupons(db, request.cart)
    return ApplicableCouponsResponse(applicable_coupons=applicable)


@router.get("/coupons/{id}/stats")
def get_coupon_stats(id: int, db: Session = Depends(get_db)):
    """Get coupon usage statistics"""
    coupon = CouponService.get_coupon_by_id(db, id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    # Base response for all coupon types
    response = {
        "coupon_id": coupon.id,
        "code": coupon.code,
        "type": coupon.type,
        "is_active": coupon.is_active,
        "expires_at": coupon.expires_at
    }
    
    # Add repetition_limit stats only for BxGy coupons
    if coupon.type == "bxgy":
        usage_percentage = 0
        if coupon.repetition_limit:
            usage_percentage = (coupon.times_used / coupon.repetition_limit) * 100
        
        response.update({
            "times_used": coupon.times_used,
            "repetition_limit": coupon.repetition_limit,
            "usage_percentage": round(usage_percentage, 2),
            "remaining_uses": coupon.repetition_limit - coupon.times_used if coupon.repetition_limit else None,
            "is_exhausted": coupon.repetition_limit and coupon.times_used >= coupon.repetition_limit
        })
    
    return response


@router.post("/apply-coupon/{id}", response_model=ApplyCouponResponse)
def apply_coupon(id: int, request: ApplyCouponRequest, db: Session = Depends(get_db)):
    """Apply a specific coupon to the cart by ID"""
    updated_cart = CouponService.apply_coupon(db, id, request.cart)
    return ApplyCouponResponse(updated_cart=updated_cart)
