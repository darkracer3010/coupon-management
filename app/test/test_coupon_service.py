"""
Unit tests for coupon service
Run with: pytest app/test/test_coupon_service.py
"""
import pytest
from app.services.coupon_service import CouponService
from app.models.schemas import Cart, CartItem


class TestCouponService:
    """Test cases for CouponService"""

    def test_calculate_cart_total(self):
        """Test cart total calculation"""
        cart = Cart(items=[
            CartItem(product_id=1, quantity=2, price=50.0),
            CartItem(product_id=2, quantity=3, price=30.0),
        ])
        total = CouponService._calculate_cart_total(cart)
        assert total == 190.0

    def test_calculate_cart_wise_discount_above_threshold(self):
        """Test cart-wise discount when cart meets threshold"""
        cart = Cart(items=[
            CartItem(product_id=1, quantity=2, price=60.0),
        ])
        details = {"threshold": 100, "discount": 10}
        discount = CouponService._calculate_cart_wise_discount(cart, details)
        assert discount == 12.0  # 10% of 120

    def test_calculate_cart_wise_discount_below_threshold(self):
        """Test cart-wise discount when cart is below threshold"""
        cart = Cart(items=[
            CartItem(product_id=1, quantity=1, price=50.0),
        ])
        details = {"threshold": 100, "discount": 10}
        discount = CouponService._calculate_cart_wise_discount(cart, details)
        assert discount == 0.0

    def test_calculate_product_wise_discount(self):
        """Test product-wise discount calculation"""
        cart = Cart(items=[
            CartItem(product_id=1, quantity=2, price=50.0),
            CartItem(product_id=2, quantity=3, price=30.0),
        ])
        details = {"product_id": 1, "discount": 20}
        discount = CouponService._calculate_product_wise_discount(cart, details)
        assert discount == 20.0  # 20% of 100

    def test_calculate_product_wise_discount_product_not_in_cart(self):
        """Test product-wise discount when product not in cart"""
        cart = Cart(items=[
            CartItem(product_id=1, quantity=2, price=50.0),
        ])
        details = {"product_id": 99, "discount": 20}
        discount = CouponService._calculate_product_wise_discount(cart, details)
        assert discount == 0.0

    def test_calculate_bxgy_discount_basic(self):
        """Test basic BxGy discount calculation"""
        cart = Cart(items=[
            CartItem(product_id=1, quantity=2, price=50.0),
            CartItem(product_id=3, quantity=1, price=25.0),
        ])
        details = {
            "buy_products": [{"product_id": 1, "quantity": 2}],
            "get_products": [{"product_id": 3, "quantity": 1}],
            "repition_limit": 1
        }
        discount = CouponService._calculate_bxgy_discount(cart, details)
        assert discount == 25.0

    def test_calculate_bxgy_discount_with_repetition(self):
        """Test BxGy discount with repetition limit"""
        cart = Cart(items=[
            CartItem(product_id=1, quantity=6, price=50.0),
            CartItem(product_id=3, quantity=3, price=25.0),
        ])
        details = {
            "buy_products": [{"product_id": 1, "quantity": 2}],
            "get_products": [{"product_id": 3, "quantity": 1}],
            "repition_limit": 3
        }
        discount = CouponService._calculate_bxgy_discount(cart, details)
        assert discount == 75.0  # 3 free items at $25 each

    def test_calculate_bxgy_discount_insufficient_buy_products(self):
        """Test BxGy when cart doesn't have enough buy products"""
        cart = Cart(items=[
            CartItem(product_id=1, quantity=1, price=50.0),
            CartItem(product_id=3, quantity=1, price=25.0),
        ])
        details = {
            "buy_products": [{"product_id": 1, "quantity": 2}],
            "get_products": [{"product_id": 3, "quantity": 1}],
            "repition_limit": 1
        }
        discount = CouponService._calculate_bxgy_discount(cart, details)
        assert discount == 0.0

    def test_calculate_bxgy_discount_limited_get_products(self):
        """Test BxGy when cart has fewer get products than eligible"""
        cart = Cart(items=[
            CartItem(product_id=1, quantity=6, price=50.0),
            CartItem(product_id=3, quantity=2, price=25.0),
        ])
        details = {
            "buy_products": [{"product_id": 1, "quantity": 2}],
            "get_products": [{"product_id": 3, "quantity": 1}],
            "repition_limit": 5
        }
        discount = CouponService._calculate_bxgy_discount(cart, details)
        # Can apply 3 times (6/2), but only 2 get products available
        assert discount == 50.0  # 2 items at $25 each
