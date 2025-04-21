import flet as ft

import sqlite3
import hashlib
import datetime
from typing import Optional, List, Dict, Tuple
import database
import exception
import helper_function
from helper_function import show_error_dialog, show_success_dialog, get_categories, get_food_items, get_image_path

# Exception handling classes
class AuthError(Exception):
    pass

class DatabaseError(Exception):
    pass

class ValidationError(Exception):
    pass

class OrderError(Exception):
    pass

# Main App
class CanteenApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self._init_search_dialog()
        self.current_food_id = None
        self.page.title = "Canteen Food Ordering System"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.on_route_change = self.route_change
        self.page.on_view_pop = self.view_pop
        self.page.go("/")

        self.routes = {
            "/": self.login_view,
            "/register": self.register_view,
            "/user_dashboard": self.user_dashboard_view,
            "/food_details": self.food_details_view,
            "/food_details/:food_id": self.food_details_view,
            "/cart": self.cart_view,
            "/checkout": self.checkout_view,
            "/order_history": self.order_history_view,
            "/order_details": self.show_order_details
        }

    def view_pop(self, view):
        # Don't allow popping the last view if it's the dashboard
        if len(self.page.views) > 1 or self.page.views[-1].route != "/user_dashboard":
            self.page.views.pop()
        
        if self.page.views:
            top_view = self.page.views[-1]
            self.page.go(top_view.route)

    def route_change(self, e):
        route = e.route if hasattr(e, 'route') else e
        print(f"Route changed to: {route}")

        # Handle food details route with ID
        if route.startswith("/food_details/"):
            parts = route.split("/")
            if len(parts) >= 3:
                try:
                    self.current_food_id = int(parts[2])
                    route = "/food_details/:food_id"
                except ValueError:
                    show_error_dialog(self.page, "Invalid food ID")
                    self.page.go("/user_dashboard")
                    return

        # Clear views if going to root
        if route == "/":
            self.page.views.clear()

        # Authentication check for protected routes
        protected_routes = [
            "/user_dashboard", "/admin_dashboard", "/food_details", 
            "/food_details/:food_id"
        ]
        
        if route in protected_routes and not helper_function.get_current_user_id(self.page):
            self.page.go("/")
            return

        # Admin routes check
        admin_routes = ["/admin_dashboard"]
        if route in admin_routes and not helper_function.is_admin(self.page):
            self.page.go("/user_dashboard")
            return

        # Get the view function from routes
        view_func = self.routes.get(route)
        if not view_func:
            show_error_dialog(self.page, "Page not found")
            self.page.go("/")
            return

        # Create the view
        view = view_func()

        # Special handling for user_dashboard - don't allow back navigation to login
        if route == "/user_dashboard":
            # Clear all views except the current one
            self.page.views.clear()
            self.page.views.append(view)
        else:
            # Normal navigation behavior for other routes
            if not self.page.views or self.page.views[-1].route != route:
                self.page.views.append(view)
                
        self.page.update()
    # Authentication Views
    def login_view(self):
        self.login_username_field = ft.TextField(label="Username", autofocus=True, width=300)
        self.login_password_field = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
        
        return ft.View(
            "/",
            [
                ft.Container(
                    content=ft.Text("Canteen Food Ordering System", size=25, weight=ft.FontWeight.BOLD),
                    padding=10,
                    border=ft.border.all(2, ft.Colors.BLACK),
                    margin=10,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Login", size=20),
                            self.login_username_field,
                            self.login_password_field,
                            ft.ElevatedButton("Login", width=300, on_click=self.login),
                            ft.TextButton("Don't have an account? Register", 
                                        on_click=lambda _: self.page.go("/register")),
                            ft.TextButton("Continue as Guest", 
                                        on_click=lambda _: self.page.go("/user_dashboard")),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=20,
                    ),
                    padding=30,
                    width=400,
                    border=ft.border.all(1, ft.Colors.GREY_400),
                    border_radius=10,
                    bgcolor=ft.Colors.WHITE,
                )
            ],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=30,
            padding=20,
            bgcolor=ft.Colors.GREY_100
        )

    def register_view(self):
        self.register_username = ft.TextField(label="Username", autofocus=True, width=300)
        self.register_email = ft.TextField(label="Email", width=300)
        self.register_phone = ft.TextField(label="Phone Number", width=300)
        self.register_password = ft.TextField(label="Password", password=True, width=300, can_reveal_password=True)
        self.register_confirm_password = ft.TextField(label="Confirm Password", password=True, can_reveal_password=True, width=300)

        return ft.View(
            "/register",
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Register", size=20, weight=ft.FontWeight.BOLD),
                            self.register_username,
                            self.register_email,
                            self.register_phone,
                            self.register_password,
                            self.register_confirm_password,
                            ft.ElevatedButton("Register", width=300, on_click=self.register),
                            ft.TextButton("Already have an account? Login", on_click=lambda _: self.page.go("/")),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                        spacing=20,
                    ),
                    padding=30,
                    width=400,
                    border=ft.border.all(1, ft.Colors.GREY_400),
                    border_radius=10,
                    bgcolor=ft.Colors.WHITE,
                )
            ],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=30,
            padding=20,
            bgcolor=ft.Colors.GREY_100
        )
    
    # User views
    def user_dashboard_view(self):
        categories = get_categories(self.page)
        food_items = get_food_items(self.page, category_id=None)
        
        category_tabs = [
            ft.Tab(text="All", icon=ft.Icons.RESTAURANT_MENU)
        ]
        for category in categories:
            category_tabs.append(ft.Tab(text=category[1], icon=ft.Icons.FASTFOOD))
        
        self.food_grid = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=200,
            child_aspect_ratio=0.85,
            spacing=10,
            run_spacing=15,
            padding=20
        )
        self.update_food_grid(food_items)
        
        return ft.View(
            "/user_dashboard",
            [
                ft.AppBar(
                    title=ft.Text("Canteen Menu"),
                    center_title=True,
                    actions=[
                        ft.IconButton(ft.Icons.SEARCH, on_click=self.show_search_dialog, tooltip="Search"),
                        ft.IconButton(ft.Icons.HISTORY, on_click=lambda _: self.page.go("/order_history"), tooltip="Order History"),
                        ft.IconButton(ft.Icons.SHOPPING_CART, on_click=lambda _: self.page.go("/cart"), tooltip="View Cart"),
                        ft.IconButton(ft.Icons.PERSON, on_click=lambda _: self.page.go("/profile"), tooltip="Profile")
                    ]
                ),
                ft.Container(
                    content=ft.Tabs(
                        tabs=category_tabs,
                        on_change=self.filter_food_by_category,
                        scrollable=True
                    ),
                    padding=ft.padding.only(bottom=10)
                ),
                ft.Container(
                    content=self.food_grid,
                    expand=True,
                    padding=10
                )
            ],
            padding=0,
            spacing=0
        )

    def food_details_view(self):
        food_id = self.current_food_id
        if not food_id:
            show_error_dialog(self.page, "No food item selected")
            self.page.go("/user_dashboard")
            return None
        
        try:
            conn = sqlite3.connect('canteen.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM food_items WHERE id=?", (food_id,))
            food_item = cursor.fetchone()

            if not food_item:
                raise DatabaseError("Food item not found")
            
            cursor.execute("SELECT name FROM categories WHERE id=?", (food_item[4],))
            category_name = cursor.fetchone()[0]
            
            # Check if item is in cart
            in_cart = False
            cart_quantity = 0
            user_id = helper_function.get_current_user_id(self.page)
            if user_id:
                cursor.execute(
                    "SELECT quantity FROM cart_items WHERE user_id=? AND food_item_id=?",
                    (user_id, food_id) 
                )
                cart_item = cursor.fetchone()
                if cart_item:
                    in_cart = True
                    cart_quantity = cart_item[0]
            
            # Get review summary
            cursor.execute(
                """
                SELECT AVG(rating), COUNT(*) 
                FROM reviews 
                WHERE food_item_id=?
                """, (food_id,)
            )
            avg_rating, review_count = cursor.fetchone()
            avg_rating = avg_rating or 0

            # Create UI elements
            self.food_quantity = ft.Text("1", size=20)
            self.food_add_to_cart_btn = ft.ElevatedButton(
                "Add to Cart" if not in_cart else f"In Cart ({cart_quantity})",
                width=200,
                on_click=lambda e: self.add_to_cart(food_id, int(self.food_quantity.value))
            )
            
            rating_stars = ft.Row(
                [ft.Icon(ft.Icons.STAR) for _ in range(int(avg_rating))] + 
                [ft.Icon(ft.Icons.STAR_OUTLINED) for _ in range(5-int(avg_rating))],
                spacing=0
            )

            return ft.View(
                f"/food_details/{food_id}",
                [
                    ft.AppBar(
                        title=ft.Text(food_item[1]),
                        leading=ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            on_click=lambda _: self.page.go("/user_dashboard"),
                            tooltip="Back to Menu"
                        ),
                        center_title=True
                    ),
                    ft.Image(
                        src=get_image_path(food_item[5]),
                        width=300,
                        height=300,
                        fit=ft.ImageFit.FILL
                    ),
                    ft.Text(f"Category: {category_name}"),
                    ft.Text(f"Price: ${food_item[3]:.2f}"),
                    ft.Row([rating_stars, ft.Text(f"{avg_rating:.1f} ({review_count})")]),
                    ft.Text(food_item[2], size=14),
                    ft.Row(
                        [
                            ft.IconButton(
                                ft.Icons.REMOVE,
                                on_click=self.decrease_quantity,
                                disabled=in_cart
                            ),
                            self.food_quantity,
                            ft.IconButton(
                                ft.Icons.ADD,
                                on_click=self.increase_quantity,
                                disabled=in_cart
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    self.food_add_to_cart_btn,
                    ft.ElevatedButton(
                        "View Reviews",
                        on_click=lambda e: self.show_reviews(food_id),
                        width=200
                    ),
                    ft.ElevatedButton(
                        "Back to Menu",
                        on_click=lambda _: self.page.go("/user_dashboard"),
                        width=200
                    )
                ],
                scroll=ft.ScrollMode.AUTO
            )
        except Exception as e:
            show_error_dialog(self.page, str(e))
            return None
        finally:
            conn.close()

    # Other methods remain the same as in your original code
    def filter_food_by_category(self, e):
        selected_idx = e.control.selected_index
        try:
            conn = sqlite3.connect('canteen.db')
            cursor = conn.cursor()
            if selected_idx == 0:
                cursor.execute("SELECT * FROM food_items WHERE available=1")
                food_items = cursor.fetchall()
                self.update_food_grid(food_items)
            else:
                cursor.execute("SELECT id FROM categories")
                categories = cursor.fetchall()
                category_id = categories[selected_idx-1][0]
                cursor.execute(
                    "SELECT * FROM food_items WHERE category_id=? AND available=1", 
                    (category_id,)
                )
                food_items = cursor.fetchall()

                if not food_items:
                    show_error_dialog(self.page, "No food items found in this category")
                    self.food_grid.controls.clear()
                    self.page.update()
                    return

                self.update_food_grid(food_items)
        except Exception as e:
            show_error_dialog(self.page, f"Error filtering food: {str(e)}")
        finally:
            conn.close()

    def update_food_grid(self, food_items):
        self.food_grid.controls.clear()

        for item in food_items:
            food_card = ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                on_tap=lambda e, item_id=item[0]: self.page.go(f"/food_details/{item_id}"),
                content=ft.Card(
                    elevation=8,
                    margin=10,
                    content=ft.Container(
                        width=180,
                        height=220,
                        padding=10,
                        content=ft.Column(
                            [
                                ft.Container(
                                    width=160,
                                    height=120,
                                    border_radius=10,
                                    content=ft.Image(
                                        src=get_image_path(item[5]),
                                        fit=ft.ImageFit.FILL,
                                        width=160,
                                        height=120,
                                    ),
                                    bgcolor=ft.Colors.GREY_200,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            item[1],
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            text_align=ft.TextAlign.CENTER,
                                            width=160,
                                            max_lines=2,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                        ft.Text(
                                            f"${item[3]:.2f}",
                                            size=14,
                                            color=ft.Colors.GREEN_700,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                    ],
                                    spacing=5,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.ElevatedButton(
                                    "View Details",
                                    on_click=lambda e, item_id=item[0]: self.page.go(f"/food_details/{item_id}"),
                                    width=160,
                                    height=30,
                                ),
                            ],
                            spacing=8,
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ),
                ),
            )
            self.food_grid.controls.append(food_card)
        
        self.page.update()

    def _init_search_dialog(self):
        """Initialize search dialog components"""
        self.search_query = ft.TextField(
            label="Search food items",
            autofocus=True,
            width=400,
            on_submit=self._perform_search
        )
        
        self.search_results = ft.ListView(expand=1, spacing=10, height=300)
        
        self.search_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Search Food"),
            content=ft.Column([
                ft.Row([
                    self.search_query,
                    ft.IconButton(
                        ft.Icons.SEARCH,
                        on_click=self._perform_search
                    )
                ]),
                ft.Divider(),
                ft.Container(
                    content=self.search_results,
                    width=450,
                    padding=10
                )
            ]),
            actions=[
                ft.TextButton("Close", on_click=self._close_search_dialog)
            ]
        )
        
        # Add to page overlay (critical for persistence)
        self.page.overlay.append(self.search_dialog)
        self.page.update()

    def show_search_dialog(self, e):
        """Show the search dialog"""
        # Reset dialog state
        self.search_query.value = ""
        self.search_results.controls.clear()
        
        # Open dialog
        self.search_dialog.open = True
        self.page.update()

    def _close_search_dialog(self, e=None):
        """Close the search dialog"""
        self.search_dialog.open = False
        self.page.update()

    def _perform_search(self, e=None):
        """Execute search and display results"""
        query = self.search_query.value.strip().lower()
        if not query:
            show_error_dialog(self.page, "Please enter a search term")
            return
        
        try:
            conn = sqlite3.connect('canteen.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM food_items WHERE (LOWER(name) LIKE ? OR LOWER(description) LIKE ?) AND available=1",
                (f"%{query}%", f"%{query}%")
            )
            results = cursor.fetchall()
            
            self.search_results.controls.clear()
            
            if not results:
                self.search_results.controls.append(
                    ft.Text("No items found", italic=True)
                )
            else:
                for item in results:
                    self.search_results.controls.append(
                        ft.ListTile(
                            leading=ft.Image(
                                src=get_image_path(item[5]),
                                width=50,
                                height=50,
                                fit=ft.ImageFit.FILL,
                                border_radius=5
                            ),
                            title=ft.Text(item[1]),
                            subtitle=ft.Text(f"${item[3]:.2f}"),
                            on_click=lambda e, item_id=item[0]: [
                                self._close_search_dialog(),
                                self.page.go(f"/food_details/{item_id}")
                            ]
                        )
                    )
            self.page.update()
        except Exception as e:
            show_error_dialog(self.page, f"Search error: {str(e)}")
        finally:
            conn.close()
    def cart_increase_quantity(self, e):
        """Handle increase quantity button click"""
        item_id = e.control.data
        self.update_cart_item(item_id, 1)

    def cart_decrease_quantity(self, e):
        """Handle decrease quantity button click"""
        item_id = e.control.data
        self.update_cart_item(item_id, -1)

    def remove_item(self, e):
        """Handle remove item button click"""
        item_id = e.control.data
        self.remove_from_cart(item_id)

    def go_to_checkout(self, e):
        """Handle checkout button click"""
        self.page.go("/checkout")

    def increase_quantity(self, e):
        current = int(self.food_quantity.value)
        self.food_quantity.value = str(current + 1)
        self.page.update()
    
    def decrease_quantity(self, e):
        current = int(self.food_quantity.value)
        if current > 1:
            self.food_quantity.value = str(current-1)
            self.page.update()

    def add_to_cart(self, food_id, quantity):
        user_id = helper_function.get_current_user_id(self.page)
        if not user_id:
            show_error_dialog(self.page, "You need to be logged in to add items to the cart")
            return
        try:
            conn = sqlite3.connect("canteen.db")
            cursor = conn.cursor()

            cursor.execute(
                "SELECT quantity FROM cart_items WHERE user_id=? AND food_item_id=?",
                (user_id, food_id)
            )
            existing_item = cursor.fetchone()
        
            if existing_item:
                new_quantity = existing_item[0] + quantity
                cursor.execute(
                    "UPDATE cart_items SET quantity=? WHERE user_id=? AND food_item_id=?",
                    (new_quantity, user_id, food_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO cart_items (user_id, food_item_id, quantity) VALUES (?, ?, ?)",
                    (user_id, food_id, quantity)
                )
            
            conn.commit()
            show_success_dialog(self.page, "Item added to cart successfully")
            self.food_add_to_cart_btn.text = f"In Cart ({new_quantity if existing_item else quantity})"
            self.page.update()
        except Exception as e:
            show_error_dialog(self.page, f"Error adding to cart: {str(e)}")
        finally: 
            conn.close()
    
    def cart_view(self):
        cart_items = self.get_cart_items()
        total = sum(item[3] * item[4] for item in cart_items)
        cart_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

        for item in cart_items:
            # Create a container for each cart item
            item_container = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Image(
                            src=get_image_path(item[5]),
                            width=60,
                            height=60,
                            fit=ft.ImageFit.COVER,
                            border_radius=ft.border_radius.all(8)
                        ),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(item[1], size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"${item[3]:.2f} x {item[4]} = ${item[3] * item[4]:.2f}", size=14),
                                ],
                                spacing=2
                            ),
                            expand=True,
                            padding=ft.padding.only(left=10)
                        ),
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.icons.REMOVE,
                                    icon_size=16,
                                    data=item[0],  # Store the item ID in the button's data attribute
                                    on_click=self.cart_decrease_quantity
                                ),
                                ft.Text(str(item[4]), size=14),
                                ft.IconButton(
                                    icon=ft.icons.ADD,
                                    icon_size=16,
                                    data=item[0],  # Store the item ID in the button's data attribute
                                    on_click=self.cart_increase_quantity
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    icon_color=ft.colors.RED_600,
                                    icon_size=18,
                                    data=item[0],  # Store the item ID in the button's data attribute
                                    on_click=self.remove_item
                                ),
                            ],
                            spacing=5
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=10,
                border=ft.border.all(0.5, ft.colors.GREY_300),
                border_radius=10,
                margin=ft.margin.symmetric(vertical=4, horizontal=8)
            )
            cart_list.controls.append(item_container)

        # Create the cart view
        cart_view = ft.View(
            "/cart",
            [
                ft.AppBar(title=ft.Text("Your Cart"),
                          leading = ft.IconButton(
                              icon=ft.Icons.ARROW_BACK,
                              on_click=lambda _: self.page.go("/user_dashboard"),
                              tooltip="Back to Menu"),
                              center_title=True
                          ),
                cart_list,
                ft.Divider(),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(f"Total: ${total:.2f}", size=18, weight=ft.FontWeight.BOLD),
                            ft.ElevatedButton(
                                "Checkout",
                                on_click=self.go_to_checkout,
                                disabled=len(cart_items) == 0
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    padding=16
                )
            ]
        )
        
        # Clear existing views and add the new one
        self.page.views.clear()
        self.page.views.append(cart_view)
        self.page.update()

    def update_cart_item(self, food_id, quantity_change):
        user_id = helper_function.get_current_user_id(self.page)
        if not user_id:
            show_error_dialog(self.page, "Please login to modify cart")
            return
        
        conn = None
        try:
            conn = sqlite3.connect('canteen.db')
            cursor = conn.cursor()
            
            # Get current quantity
            cursor.execute(
                "SELECT quantity FROM cart_items WHERE user_id=? AND food_item_id=?",
                (user_id, food_id)
            )
            result = cursor.fetchone()
            
            if not result:
                show_error_dialog(self.page, "Item not found in cart")
                return
                
            current_quantity = result[0]
            new_quantity = current_quantity + quantity_change
            
            if new_quantity <= 0:
                # Remove item if quantity reaches 0
                cursor.execute(
                    "DELETE FROM cart_items WHERE user_id=? AND food_item_id=?",
                    (user_id, food_id)
                )
            else:
                # Update quantity
                cursor.execute(
                    "UPDATE cart_items SET quantity=? WHERE user_id=? AND food_item_id=?",
                    (new_quantity, user_id, food_id)
                )
            
            conn.commit()
            # Refresh the cart view
            self.cart_view()
            
        except Exception as e:
            show_error_dialog(self.page, f"Failed to update cart: {str(e)}")
            import traceback
            traceback.print_exc()  # Print full traceback for debugging
        finally:
            if conn:
                conn.close()
    def remove_from_cart(self, food_id):
        user_id = helper_function.get_current_user_id(self.page)
        if not user_id:
            show_error_dialog(self.page, "Please login to remove items from cart")
            return
        
        try:
            conn = sqlite3.connect('canteen.db')
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM cart_items WHERE user_id=? AND food_item_id=?",
                (user_id, food_id)
            )
            conn.commit()
            self.cart_view()
            show_success_dialog(self.page, "Item removed from cart successfully")
        except Exception as e:
            show_error_dialog(self.page, f"Error removing item from cart: {str(e)}")
        finally:
            conn.close()

    def checkout_view(self):
        cart_items = self.get_cart_items()
        total = sum(item[3] * item[4] for item in cart_items)
        order_summary = ft.Column()
        for item in cart_items:
            order_summary.controls.append(
                ft.Text(f"{item[1]} x {item[4]} = ${item[3] * item[4]:.2f}", size=16)
            )
        
        order_summary.controls.append(
            ft.Text(f"Total: ${total:.2f}", weight=ft.FontWeight.BOLD)
        )
        self.checkout_address = ft.TextField(
            label="Delivery Address",
            width=400,
            multiline=True,
            max_lines=4,
            min_lines=2,
        )

        self.payment_method = ft.RadioGroup(
            content=ft.Column([
                ft.Radio(value="cash", label="Cash on Delivery"),
                ft.Radio(value="card", label="Credit/Debit Card")
            ]),
            value="cash"
        )
        self.page.views.append(
            ft.View(
                "/checkout",
                [
                    ft.AppBar(title=ft.Text("Checkout")),
                    ft.Text("Order Summary", size=18),
                    ft.Container(
                        content=order_summary,
                        padding=10,
                        border=ft.border.all(1, ft.colors.GREY_300),
                        border_radius=5,
                        margin=10
                    ),
                    self.checkout_address,
                    ft.Text("Payment Method", size=16),
                    self.payment_method,
                    ft.ElevatedButton(
                        "Place Order", 
                        on_click=self.place_order,
                        width=200
                    )
                ],
                scroll=ft.ScrollMode.AUTO
            )
        )
    def place_order(self, e):
        user_id = helper_function.get_current_user_id(self.page)
        if not user_id:
            show_error_dialog(self.page, "Please login to place an order")
            return
        cart_items = self.get_cart_items()
        if not cart_items:
            show_error_dialog(self.page, "Your cart is empty")
            return
        address = self.checkout_address.value.strip()
        if not address:
            show_error_dialog(self.page, "Delivery address is required")
            return 
        
        try:
            conn = sqlite3.connect('canteen.db')
            cursor = conn.cursor()
            
            # Calculate total
            total = sum(item[3] * item[4] for item in cart_items)
            
            # Create order
            cursor.execute(
                "INSERT INTO orders (user_id, total_amount) VALUES (?, ?)",
                (user_id, total)
            )
            order_id = cursor.lastrowid
            
            # Add order items
            for item in cart_items:
                cursor.execute(
                    """INSERT INTO order_items 
                    (order_id, food_item_id, quantity, price_at_order) 
                    VALUES (?, ?, ?, ?)""",
                    (order_id, item[0], item[4], item[3])
                )
            
            # Clear cart
            cursor.execute("DELETE FROM cart_items WHERE user_id=?", (user_id,))
            
            conn.commit()
            show_success_dialog(self.page, "Order placed successfully!")
            self.page.go("/user_dashboard")
            
        except Exception as e:
            conn.rollback()
            show_error_dialog(self.page, f"Order failed: {str(e)}")
            raise OrderError(f"Order processing error: {str(e)}")
        finally:
            conn.close()
    
    def order_history_view(self):
        user_id = helper_function.get_current_user_id(self.page)
        if not user_id:
            show_error_dialog(self.page, "Please login to view order history")
            return

        try:
            conn = sqlite3.connect('canteen.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, order_date, status, total_amount 
                FROM orders 
                WHERE user_id=?
                ORDER BY order_date DESC
            """, (user_id,))
            orders = cursor.fetchall()

            order_list = ft.ListView(expand=1)
            for order in orders:
                status_color = {
                    'pending': ft.colors.ORANGE,
                    'accepted': ft.colors.BLUE,
                    'prepared': ft.colors.PURPLE,
                    'delivered': ft.colors.GREEN,
                    'rejected': ft.colors.RED
                }.get(order[2], ft.colors.GREY)
                
                order_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(f"Order #{order[0]}"),
                        subtitle=ft.Column([
                            ft.Text(f"Date: {order[1]}"),
                            ft.Text(f"Total: ${order[3]:.2f}"),
                            ft.Text(f"Status: {order[2]}", color=status_color)
                        ]),
                        on_click=lambda e, oid=order[0]: self.show_order_details(oid)
                    )
                )
            
            self.page.views.append(
                ft.View(
                    "/order_history",
                    [
                        ft.AppBar(title=ft.Text("Order History")),
                        order_list
                    ]
                )
            )
            self.page.update()
            
        except Exception as e:
            show_error_dialog(self.page, f"Failed to load orders: {str(e)}")
        finally:
            conn.close()
    
    def show_order_details(self, order_id):
        try:
            conn = sqlite3.connect('canteen.db')
            cursor = conn.cursor()
            
            # Get order info
            cursor.execute("""
                SELECT o.order_date, o.status, o.total_amount, u.username 
                FROM orders o
                JOIN users u ON o.user_id = u.id
                WHERE o.id=?
            """, (order_id,))
            order_info = cursor.fetchone()
            
            # Get order items
            cursor.execute("""
                SELECT fi.name, oi.quantity, oi.price_at_order 
                FROM order_items oi
                JOIN food_items fi ON oi.food_item_id = fi.id
                WHERE oi.order_id=?
            """, (order_id,))
            order_items = cursor.fetchall()
            
            # Create order summary
            order_summary = ft.Column()
            for item in order_items:
                order_summary.controls.append(
                    ft.Text(f"{item[0]} x {item[1]} = ${item[1] * item[2]:.2f}")
                )
            
            status_color = {
                'pending': ft.colors.ORANGE,
                'accepted': ft.colors.BLUE,
                'prepared': ft.colors.PURPLE,
                'delivered': ft.colors.GREEN,
                'rejected': ft.colors.RED
            }.get(order_info[1], ft.colors.GREY)
            
            self.page.views.append(
                ft.View(
                    "/order_details/{order_id}",
                    [
                        ft.AppBar(title=ft.Text(f"Order #{order_id}")),
                        ft.Text(f"Customer: {order_info[3]}"),
                        ft.Text(f"Date: {order_info[0]}"),
                        ft.Text(f"Status: {order_info[1]}", color=status_color),
                        ft.Text(f"Total: ${order_info[2]:.2f}", size=16, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        ft.Text("Items:", size=14, weight=ft.FontWeight.BOLD),
                        order_summary,
                        ft.Divider(),
                    ],
                    scroll=ft.ScrollMode.AUTO
                )
            )
            self.page.update()
            
        except Exception as e:
            show_error_dialog(self.page, f"Failed to load order details: {str(e)}")
        finally:
            conn.close()

    def show_reviews(self, food_id):
        # Implement reviews display
        show_error_dialog(self.page, "Reviews feature not implemented yet")
    
    #Admin Dashboard Views
    def admin_dashboard_view(self):
        stats = self.get_admin_stats()
        
        stats_row = ft.Row([
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Total Orders", size=16),
                        ft.Text(stats['total_orders'], size=24, weight=ft.FontWeight.BOLD)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20,
                    width=150,
                    height=150
                )
            ),
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Pending Orders", size=16),
                        ft.Text(stats['pending_orders'], size=24, weight=ft.FontWeight.BOLD)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20,
                    width=150,
                    height=150
                )
            ),
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Total Food Items", size=16),
                        ft.Text(stats['total_food_items'], size=24, weight=ft.FontWeight.BOLD)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20,
                    width=150,
                    height=150
                )
            ),
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Total Customers", size=16),
                        ft.Text(stats['total_customers'], size=24, weight=ft.FontWeight.BOLD)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20,
                    width=150,
                    height=150
                )
            )
        ], spacing=20, wrap=True)
        
        quick_actions = ft.Row([
            ft.ElevatedButton(
                "Manage Categories",
                icon=ft.icons.CATEGORY,
                on_click=lambda _: self.page.go("/food_categories")
            ),
            ft.ElevatedButton(
                "Manage Food Items",
                icon=ft.icons.RESTAURANT,
                on_click=lambda _: self.page.go("/manage_food")
            ),
            ft.ElevatedButton(
                "View Orders",
                icon=ft.icons.LIST_ALT,
                on_click=lambda _: self.page.go("/view_orders")
            )
        ], spacing=10)
        
        self.page.views.append(
            ft.View(
                "/admin_dashboard",
                [
                    ft.AppBar(
                        title=ft.Text("Admin Dashboard"),
                        actions=[
                            ft.PopupMenuButton(
                                items=[
                                    ft.PopupMenuItem(
                                        text="Profile",
                                        icon=ft.icons.PERSON,
                                        on_click=lambda _: self.page.go("/profile")
                                    ),
                                    ft.PopupMenuItem(
                                        text="Logout",
                                        icon=ft.icons.LOGOUT,
                                        on_click=self.logout
                                    )
                                ]
                            )
                        ]
                    ),
                    ft.Text("Overview", size=20),
                    stats_row,
                    ft.Divider(),
                    ft.Text("Quick Actions", size=20),
                    quick_actions
                ],
                scroll=ft.ScrollMode.AUTO
            )
        )
    
    def add_category_dialog(self, e):
        pass
    def edit_category_dialog(self, e):
        pass
    def delete_category_dialog(self, e):
        pass
    def save_category(self, e):
        pass
    def update_category(self, e):
        pass
    def delete_category(self, e):
        pass
    def manage_food_view(self):
        pass
    def add_food_dialog(self, e):
        pass
    def handle_file_upload(self, e:ft.FilePickerResultEvent):
        pass
    def save_food_item(self, e):
        pass
    def edit_food_dialog(self, e):
        pass
    def update_food_item(self, e):
        pass
    def delete_food_dialog(self, food_id):
        pass
    def delete_food_item(self, e):
        pass
    def view_orders_view(self):
        pass
    def update_order_status(self, e):
        pass
    def profile_view(self):
        pass
    def update_password(self, e):
        pass
    def get_admin_stats(self) -> Dict:
        try:
            conn = sqlite3.connect('canteen.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM orders")
            total_orders = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status='pending'")
            pending_orders = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM food_items")
            total_food_items = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin=0")
            total_customers = cursor.fetchone()[0]
            
            return {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'total_food_items': total_food_items,
                'total_customers': total_customers
            }
        except Exception as e:
            show_error_dialog(self.page, str(e))
            return {}
        finally:
            conn.close()

    # Authentication methods
    def login(self, e):
        username = self.login_username_field.value
        password = self.login_password_field.value

        if not username or not password:
            show_error_dialog(self.page, "Username and password are required")
            return
        
        conn = None
        try:
            conn = sqlite3.connect('canteen.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, password, is_admin FROM users WHERE username=?",
                (username,)
            )
            user = cursor.fetchone()

            if not user:
                raise AuthError("Invalid username or password")
            if not helper_function.verify_password(user[1], password):
                raise AuthError("Invalid username or password")
            
            # Store user session
            self.page.client_storage.set("user_id", user[0])
            self.page.client_storage.set("is_admin", bool(user[2]))

            # Redirect based on role
            if user[2]:
                self.page.go("/admin_dashboard")
            else:
                self.page.go("/user_dashboard")
        except AuthError as e:
            show_error_dialog(self.page, str(e))
        except Exception as e:
            show_error_dialog(self.page, "An error occurred during login")
            print(f"Login error: {str(e)}")
        finally:
            if conn:
                conn.close()

    def register(self, e):
        username = self.register_username.value
        email = self.register_email.value
        phone = self.register_phone.value
        password = self.register_password.value
        confirm_password = self.register_confirm_password.value

        if not all([username, email, password, confirm_password]):
            show_error_dialog(self.page, "All fields except phone are required")
            return
        
        if password != confirm_password:
            show_error_dialog(self.page, "Passwords don't match")
            return

        try:
            conn = sqlite3.connect('canteen.db')
            cursor = conn.cursor()
            hashed_password = helper_function.hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, email, phone, password) VALUES (?, ?, ?, ?)",
                (username, email, phone, hashed_password)
            )
            conn.commit()

            show_success_dialog(self.page, "Registration successful! Please login.")
            self.page.go("/")

        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                show_error_dialog(self.page, "Username already exists")
            elif "email" in str(e):
                show_error_dialog(self.page, "Email already exists")
            else:
                show_error_dialog(self.page, "Registration failed")
        
        except Exception as e:
            show_error_dialog(self.page, str(e))
        finally:
            if conn:
                conn.close()
    
    def logout(self, e):
        self.page.client_storage.remove("user_id")
        self.page.client_storage.remove("is_admin")
        self.page.go("/")
    
    def get_cart_items(self) -> List[Tuple]:
        user_id = helper_function.get_current_user_id(self.page)
        if not user_id:
            return []
        
        try:
            conn = sqlite3.connect('canteen.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT fi.id, fi.name, fi.description, fi.price, ci.quantity, fi.image_path
                FROM cart_items ci
                JOIN food_items fi ON ci.food_item_id = fi.id
                WHERE ci.user_id=?
            ''', (user_id,))
            return cursor.fetchall()
        except Exception as e:
            show_error_dialog(self.page, str(e))
            return []
        finally:
            conn.close()

def main(page: ft.Page):
    app = CanteenApp(page)

ft.app(target=main)

