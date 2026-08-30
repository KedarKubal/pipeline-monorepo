-- Seeds a legacy-style denormalized orders table for local/demo runs.
-- In production this would be the actual legacy vendor database instead.
CREATE TABLE IF NOT EXISTS orders_legacy (
    order_id VARCHAR(64),
    cust_id VARCHAR(64),
    product_sku VARCHAR(64),
    product_name VARCHAR(255),
    qty INTEGER,
    unit_price NUMERIC(10, 2),
    order_date VARCHAR(32),
    status VARCHAR(32)
);

INSERT INTO orders_legacy (order_id, cust_id, product_sku, product_name, qty, unit_price, order_date, status) VALUES
('O1001', 'C001', 'SKU-100', 'Widget Large', 2, 19.99, '2023-06-01', 'shipped'),
('O1001', 'C001', 'SKU-200', 'Widget Small', 1, 9.99, '2023-06-01', 'shipped'),
('O1002', 'C002', 'SKU-100', 'Widget Large', 1, 19.99, '2023-06-15', 'delivered'),
('O1003', 'C999', 'SKU-300', 'Widget Medium', 3, 14.99, '2023-07-01', 'pending'),  -- orphaned customer
('O1004', 'C003', 'SKU-200', 'Widget Small', 0, 9.99, '2023-07-10', 'cancelled'),   -- invalid qty
('O1005', 'C002', 'SKU-400', 'Widget XL', -1, 24.99, '2023-07-20', 'pending');      -- invalid price/qty
