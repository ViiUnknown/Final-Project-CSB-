import sqlite3
import hashlib
#Database
def init_db():
    conn = sqlite3.connect('canteen.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        is_admin BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Categories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    )''')
    
    # Food items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS food_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        category_id INTEGER NOT NULL,
        image_path TEXT,
        available BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    )''')
    
    # Orders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending', -- pending, accepted, rejected, prepared, delivered
        total_amount REAL NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Order items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        food_item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price_at_order REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (food_item_id) REFERENCES food_items(id)
    )''')
    
    # Reviews table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        food_item_id INTEGER NOT NULL,
        order_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        comment TEXT,
        review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (food_item_id) REFERENCES food_items(id),
        FOREIGN KEY (order_id) REFERENCES orders(id)
    )''')
    
    # Create admin if not exists
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        hashed_password = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute(
            "INSERT INTO users (username, password, email, is_admin) VALUES (?, ?, ?, ?)",
            ('admin', hashed_password, 'admin@canteen.com', True)
        )
    
    conn.commit()
    conn.close()

init_db()

conn = sqlite3.connect('canteen.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()
for user in users:
    print(user)

conn.close()