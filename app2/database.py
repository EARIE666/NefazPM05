import sqlite3


class Database:
    def __init__(self, db_name="warehouse.db"):
        self.conn = sqlite3.connect(db_name)
        self.cur = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                article TEXT,
                unit TEXT,
                category_id INTEGER,
                quantity REAL DEFAULT 0,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                type TEXT,
                amount REAL,
                date TEXT,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        self.conn.commit()

    # ---- Категории ----
    def add_category(self, name):
        self.cur.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        self.conn.commit()

    def get_categories(self):
        self.cur.execute("SELECT * FROM categories")
        return self.cur.fetchall()

    # ---- Товары ----
    def add_product(self, name, article, unit, category_id):
        self.cur.execute(
            "INSERT INTO products (name, article, unit, category_id, quantity) "
            "VALUES (?, ?, ?, ?, 0)",
            (name, article, unit, category_id)
        )
        self.conn.commit()

    def update_product(self, pid, name, article, unit):
        self.cur.execute(
            "UPDATE products SET name=?, article=?, unit=? WHERE id=?",
            (name, article, unit, pid)
        )
        self.conn.commit()

    def delete_product(self, pid):
        self.cur.execute("DELETE FROM products WHERE id=?", (pid,))
        self.cur.execute("DELETE FROM operations WHERE product_id=?", (pid,))
        self.conn.commit()

    def get_products(self, search=""):
        if search:
            self.cur.execute(
                "SELECT * FROM products WHERE name LIKE ? OR article LIKE ?",
                (f"%{search}%", f"%{search}%")
            )
        else:
            self.cur.execute("SELECT * FROM products")
        return self.cur.fetchall()

    def get_product_quantity(self, pid):
        self.cur.execute("SELECT quantity FROM products WHERE id=?", (pid,))
        row = self.cur.fetchone()
        return row[0] if row else 0

    # ---- Операции ----
    def add_operation(self, product_id, op_type, amount, date):
        if op_type == "Расход":
            current = self.get_product_quantity(product_id)
            if amount > current:
                raise ValueError("Недостаточно товара на складе!")
            new_qty = current - amount
        else:
            current = self.get_product_quantity(product_id)
            new_qty = current + amount

        self.cur.execute(
            "INSERT INTO operations (product_id, type, amount, date) "
            "VALUES (?, ?, ?, ?)",
            (product_id, op_type, amount, date)
        )
        self.cur.execute(
            "UPDATE products SET quantity=? WHERE id=?",
            (new_qty, product_id)
        )
        self.conn.commit()

    def get_operations(self):
        self.cur.execute("""
            SELECT operations.id, products.name, operations.type,
                   operations.amount, operations.date
            FROM operations
            JOIN products ON operations.product_id = products.id
            ORDER BY operations.date DESC
        """)
        return self.cur.fetchall()

    def close(self):
        self.conn.close()