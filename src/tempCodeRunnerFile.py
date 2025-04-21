import sqlite3
from tabulate import tabulate

def show_all_food_items():
    conn = sqlite3.connect('canteen.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT food_items.id, food_items.name, food_items.description, 
               food_items.price, categories.name AS category_name, 
               food_items.available, food_items.image_path
        FROM food_items
        JOIN categories ON food_items.category_id = categories.id
    ''')

    rows = cursor.fetchall()
    
    headers = ["ID", "Name", "Description", "Price ($)", "Category", "Available", "Image Path"]
    
    # Convert boolean available to "Yes"/"No"
    table_data = [
        [
            row[0], row[1], row[2], f"{row[3]:.2f}", row[4],
            "Yes" if row[5] else "No", row[6]
        ]
        for row in rows
    ]

    print("\nAll Food Items:\n")
    print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))

    conn.close()

# Call the function to test it
show_all_food_items()