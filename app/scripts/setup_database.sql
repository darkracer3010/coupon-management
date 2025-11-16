-- Coupon Management API - Complete Database Setup
-- PostgreSQL Setup Script

-- ============================================
-- Create Database
-- ============================================
-- This creates the database if it doesn't exist
-- Note: Run this file with: psql -U postgres -f setup_database.sql

-- Drop database if exists (WARNING: This will delete all data!)
-- Uncomment the line below if you want to start fresh
-- DROP DATABASE IF EXISTS coupons_db;

-- Create database
CREATE DATABASE coupons_db;

-- Display success message
\echo 'Database coupons_db created successfully!'
\echo 'Now connecting to coupons_db...'

-- Connect to the new database
\c coupons_db

-- ============================================
-- Create Tables
-- ============================================

-- Drop table if exists (for clean setup)
DROP TABLE IF EXISTS coupons CASCADE;

-- Create coupons table
CREATE TABLE coupons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,
    details JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Asia/Kolkata'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Asia/Kolkata'),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    repetition_limit INTEGER,
    times_used INTEGER DEFAULT 0,
    
    -- Constraints
    CONSTRAINT valid_coupon_type CHECK (type IN ('cart-wise', 'product-wise', 'bxgy')),
    CONSTRAINT valid_times_used CHECK (times_used >= 0),
    CONSTRAINT valid_repetition_limit CHECK (repetition_limit IS NULL OR repetition_limit > 0),
    CONSTRAINT valid_code_format CHECK (code ~ '^[A-Za-z0-9]+$' AND LENGTH(code) >= 4)
);

-- Create indexes for better query performance
CREATE INDEX idx_coupons_code ON coupons(code);
CREATE INDEX idx_coupons_type ON coupons(type);
CREATE INDEX idx_coupons_is_active ON coupons(is_active);
CREATE INDEX idx_coupons_expires_at ON coupons(expires_at);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW() AT TIME ZONE 'Asia/Kolkata';
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to call the function
CREATE TRIGGER update_coupons_updated_at 
    BEFORE UPDATE ON coupons
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data (optional)
INSERT INTO coupons (code, type, details, repetition_limit) VALUES
(
    'SAVE10',
    'cart-wise',
    '{"threshold": 100, "discount": 10}'::jsonb,
    NULL
),
(
    'PRODUCT20',
    'product-wise',
    '{"product_id": 1, "discount": 20}'::jsonb,
    NULL
),
(
    'BUY2GET1',
    'bxgy',
    '{"buy_products": [{"product_id": 1, "quantity": 3}, {"product_id": 2, "quantity": 3}], "get_products": [{"product_id": 3, "quantity": 1}]}'::jsonb,
    2
);

-- Verify table creation
\echo ''
\echo '============================================'
\echo 'Table Structure:'
\echo '============================================'
\d coupons

-- Display sample data
\echo ''
\echo '============================================'
\echo 'Sample Data:'
\echo '============================================'
SELECT id, code, type, is_active, created_at FROM coupons;

\echo ''
\echo '============================================'
\echo 'Setup Complete!'
\echo '============================================'
\echo 'Database: coupons_db'
\echo 'Table: coupons'
\echo 'Sample coupons: 3'
\echo ''
\echo 'You can now run: python main.py'
\echo '============================================'
