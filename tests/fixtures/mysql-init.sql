-- MySQL 测试数据库初始化脚本
-- 创建测试表和示例数据

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) UNIQUE,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_email (email),
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    shipping_address TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_order_date (order_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单信息表';

-- 订单项表
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_order_id (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单项表';

-- 产品表
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_code VARCHAR(50) NOT NULL UNIQUE,
    product_name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='产品信息表';

-- 插入测试数据
INSERT INTO users (username, email, full_name, is_active) VALUES
    ('alice', 'alice@example.com', 'Alice Smith', TRUE),
    ('bob', 'bob@example.com', 'Bob Johnson', TRUE),
    ('charlie', 'charlie@example.com', 'Charlie Brown', FALSE),
    ('david', 'david@example.com', 'David Wilson', TRUE),
    ('eve', 'eve@example.com', 'Eve Davis', TRUE);

INSERT INTO products (product_code, product_name, description, price, stock_quantity, category) VALUES
    ('PROD001', '笔记本电脑', '高性能办公笔记本', 5999.00, 50, '电子产品'),
    ('PROD002', '无线鼠标', '人体工学设计', 99.00, 200, '电子产品'),
    ('PROD003', '机械键盘', 'RGB背光机械键盘', 399.00, 100, '电子产品'),
    ('PROD004', '显示器', '27寸4K显示器', 2999.00, 30, '电子产品'),
    ('PROD005', '办公椅', '人体工学办公椅', 1299.00, 20, '家具');

INSERT INTO orders (user_id, order_number, total_amount, status, shipping_address) VALUES
    (1, 'ORD20250101001', 6497.00, 'completed', '北京市朝阳区xxx街道xxx号'),
    (1, 'ORD20250102001', 399.00, 'shipped', '北京市朝阳区xxx街道xxx号'),
    (2, 'ORD20250103001', 3098.00, 'pending', '上海市浦东新区xxx路xxx号'),
    (4, 'ORD20250104001', 1299.00, 'completed', '深圳市南山区xxx大道xxx号'),
    (5, 'ORD20250105001', 5999.00, 'processing', '广州市天河区xxx路xxx号');

INSERT INTO order_items (order_id, product_name, quantity, unit_price, subtotal) VALUES
    (1, '笔记本电脑', 1, 5999.00, 5999.00),
    (1, '无线鼠标', 1, 99.00, 99.00),
    (1, '机械键盘', 1, 399.00, 399.00),
    (2, '机械键盘', 1, 399.00, 399.00),
    (3, '显示器', 1, 2999.00, 2999.00),
    (3, '无线鼠标', 1, 99.00, 99.00),
    (4, '办公椅', 1, 1299.00, 1299.00),
    (5, '笔记本电脑', 1, 5999.00, 5999.00);

-- 创建视图
CREATE OR REPLACE VIEW user_order_summary AS
SELECT 
    u.id AS user_id,
    u.username,
    u.email,
    COUNT(o.id) AS total_orders,
    COALESCE(SUM(o.total_amount), 0) AS total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username, u.email;
