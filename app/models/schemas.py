from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CouponType(str, Enum):
    CART_WISE = "cart-wise"
    PRODUCT_WISE = "product-wise"
    BXGY = "bxgy"


class CartWiseDetails(BaseModel):
    threshold: float = Field(..., gt=0, description="Minimum cart value")
    discount: float = Field(..., gt=0, le=100, description="Discount percentage")


class ProductWiseDetails(BaseModel):
    product_id: int = Field(..., gt=0)
    discount: float = Field(..., gt=0, le=100, description="Discount percentage")


class BxGyProduct(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class BxGyDetails(BaseModel):
    buy_products: List[BxGyProduct]
    get_products: List[BxGyProduct]
    repition_limit: int = Field(default=1, ge=1)


class CouponCreate(BaseModel):
    code: str = Field(..., min_length=4, max_length=50, pattern=r'^[A-Za-z0-9]+$')
    type: CouponType
    details: Dict[str, Any]
    expires_at: Optional[datetime] = None
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Ensure code is alphanumeric"""
        if not v.isalnum():
            raise ValueError('Coupon code must be alphanumeric (letters and numbers only)')
        return v


class CouponUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=4, max_length=50, pattern=r'^[A-Za-z0-9]+$')
    type: Optional[CouponType] = None
    details: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        """Ensure code is alphanumeric"""
        if v is not None:
            if not v.isalnum():
                raise ValueError('Coupon code must be alphanumeric (letters and numbers only)')
        return v


class CouponResponse(BaseModel):
    id: int
    code: str
    type: str
    details: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    repetition_limit: Optional[int]
    times_used: int

    class Config:
        from_attributes = True


class CartItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)


class Cart(BaseModel):
    items: List[CartItem]


class ApplicableCouponsRequest(BaseModel):
    cart: Cart


class ApplicableCoupon(BaseModel):
    coupon_id: int
    type: str
    discount: float


class ApplicableCouponsResponse(BaseModel):
    applicable_coupons: List[ApplicableCoupon]


class UpdatedCartItem(BaseModel):
    product_id: int
    quantity: int
    price: float
    total_discount: float


class UpdatedCart(BaseModel):
    items: List[UpdatedCartItem]
    total_price: float
    total_discount: float
    final_price: float


class ApplyCouponRequest(BaseModel):
    cart: Cart


class ApplyCouponResponse(BaseModel):
    updated_cart: UpdatedCart
