-- 테스트용 초기 데이터
-- AI Platform MySQL MCP 테스트용

-- 고객 테이블
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 주문 테이블
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(20) NOT NULL UNIQUE,
    customer_id INT NOT NULL,
    total_amount DECIMAL(15, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    order_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- 상품 테이블
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(15, 2) NOT NULL,
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 테스트 데이터 삽입
INSERT INTO customers (customer_code, name, email, phone) VALUES
('C001', '삼성전자', 'contact@samsung.com', '02-1234-5678'),
('C002', 'LG전자', 'contact@lg.com', '02-2345-6789'),
('C003', 'SK하이닉스', 'contact@skhynix.com', '031-789-0123'),
('C004', '현대자동차', 'contact@hyundai.com', '02-3456-7890'),
('C005', 'NAVER', 'contact@naver.com', '1588-3820');

INSERT INTO products (product_code, name, price, stock) VALUES
('P001', 'AI 플랫폼 라이선스 (1년)', 12000000, 100),
('P002', 'AI 플랫폼 라이선스 (월간)', 1200000, 100),
('P003', '기술 지원 패키지', 5000000, 50),
('P004', '맞춤 개발 서비스', 30000000, 10),
('P005', '교육 프로그램', 2000000, 30);

INSERT INTO orders (order_number, customer_id, total_amount, status, order_date) VALUES
('ORD-2024-001', 1, 36000000, 'completed', '2024-12-01'),
('ORD-2024-002', 2, 12000000, 'completed', '2024-12-05'),
('ORD-2024-003', 3, 17000000, 'completed', '2024-12-10'),
('ORD-2024-004', 1, 5000000, 'pending', '2024-12-15'),
('ORD-2024-005', 4, 30000000, 'processing', '2024-12-20'),
('ORD-2024-006', 5, 14000000, 'completed', '2024-12-25');
