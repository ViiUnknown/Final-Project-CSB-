import flet as ft
import hashlib
import sqlite3
from typing import Optional, List, Dict, Tuple
import os
from pathlib import Path
#Helper Functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(hashed_password: str, user_password: str) -> bool:
    return hashed_password == hash_password(user_password)

def get_current_user_id(page: ft.Page) -> Optional[int]:
    return page.client_storage.get("user_id")

def is_admin(page: ft.Page) -> bool:
    return page.client_storage.get("is_admin") or False

#Helper Method
def show_error_dialog(page: ft.Page, message: str):
    def close_dialog(e=None):
        dialog.open = False
        page.update()

    dialog = ft.AlertDialog(
        title=ft.Text("Error"),
        content=ft.Text(message),
        actions=[ft.TextButton("OK", on_click=close_dialog)]
    )
    page.overlay.append(dialog)
    dialog.open = True
    page.update()

def show_success_dialog(page: ft.Page, message:str):
    def close_dialog(e=None):
        dialog.open = False
        page.update()

    dialog = ft.AlertDialog(
        title=ft.Text("Success"),
        content=ft.Text(message),
        actions=[ft.TextButton("OK", on_click=close_dialog)]
    )
    page.overlay.append(dialog)
    dialog.open = True
    page.update()

def show_view(page: ft.Page, view):
    page.views.append(view)
    page.update()

def get_categories(page: ft.Page) -> List[Tuple]:
    try:
        conn = sqlite3.connect('canteen.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY name")
        return cursor.fetchall()
    except Exception as e:
        show_error_dialog(page, str(e))
        return []
    finally:
        conn.close()

def get_food_items(page: ft.Page, category_id: Optional[int] = None) -> List[Tuple]:
    try:
        conn = sqlite3.connect('canteen.db')
        cursor = conn.cursor()

        if category_id:
            cursor.execute(
            "SELECT * FROM food_items WHERE category_id=? AND available=1",
                    (category_id,)
            )
        else:
            cursor.execute("SELECT * FROM food_items WHERE available=1")

        return cursor.fetchall()
    except Exception as e:
        show_error_dialog(page, str(e))

import os
from pathlib import Path

# Add this right after your imports
def get_image_path(db_path=None):
    """Handles all image paths consistently"""
    # 1. Define possible locations
    assets_dir = Path("assets")
    absolute_assets = Path("E:/TO-DO-LIST-Project/SchoolProject/CSB_Final_Project/src/assets")
    
    # 2. Determine which assets location exists
    working_assets = absolute_assets if absolute_assets.exists() else assets_dir
    
    # 3. Handle default image
    default_image = working_assets / "default.png"
    
    # 4. Return the appropriate path
    if db_path:
        potential_path = working_assets / db_path
        if potential_path.exists():
            return str(potential_path)
    return str(default_image)