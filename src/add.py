import sqlite3
import os

# def verify_image_files():
#     conn = sqlite3.connect('canteen.db')
#     cursor = conn.cursor()
#     cursor.execute("SELECT id, name, image_path FROM food_items")
    
#     missing_files = []
#     for item in cursor.fetchall():
#         if not os.path.exists(item[2]):  # Check if file exists at path
#             missing_files.append((item[0], item[1], item[2]))
    
#     if missing_files:
#         print(f"⚠️ Missing {len(missing_files)} image files:")
#         for item in missing_files:
#             print(f"ID {item[0]}: {item[1]} -> {item[2]}")
#     else:
#         print("✅ All image files exist!")
    
#     conn.close()

# verify_image_files()

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

# import sqlite3

# def clean_image_paths():
#     conn = sqlite3.connect('canteen.db')
#     cursor = conn.cursor()

#     # Update all image_path values by removing 'assets/' from the beginning
#     cursor.execute('''
#         UPDATE food_items
#         SET image_path = REPLACE(image_path, 'assets/', '')
#         WHERE image_path LIKE 'assets/%'
#     ''')

#     conn.commit()
#     conn.close()
#     print("Image paths updated successfully!")

# # Run the function
# clean_image_paths()

# import sqlite3

# def convert_jpg_to_png():
#     conn = sqlite3.connect('canteen.db')
#     cursor = conn.cursor()

#     # Replace all image paths ending in .jpg with .png
#     cursor.execute('''
#         UPDATE food_items
#         SET image_path = REPLACE(image_path, '.jpg', '.png')
#         WHERE image_path LIKE '%.jpg'
#     ''')

#     conn.commit()
#     conn.close()
#     print("Image extensions updated from .jpg to .png!")

# # Run the function
# convert_jpg_to_png()
