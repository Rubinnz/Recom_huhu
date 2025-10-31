import mysql.connector

DB_CFG = {
    "host": "b5fsacyipaetgcqkwacb-mysql.services.clever-cloud.com",
    "user": "uzffiaml7jzguazv",
    "password": "o9O1qqAb2XjXtYN0b4kc",
    "database": "b5fsacyipaetgcqkwacb",
    "port": 3306,
}

def main():
    conn = mysql.connector.connect(**DB_CFG)
    cur = conn.cursor()

    # Xóa bảng cũ nếu có (cẩn thận: sẽ mất dữ liệu user cũ)
    cur.execute("DROP TABLE IF EXISTS users")

    # Tạo bảng mới với cột last_login
    cur.execute("""
    CREATE TABLE users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(64) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP NULL DEFAULT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Bảng users đã được tạo lại thành công (có last_login).")

if __name__ == "__main__":
    main()
