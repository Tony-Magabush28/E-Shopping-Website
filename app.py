from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# In-memory data (replace with a database in real app)
products = [
    {"id": 1, "name": "Premium Coffee", "description": "Freshly roasted premium coffee beans from Ghana.", "price": 120.00, "image": "c.jpg"},
    {"id": 2, "name": "Handmade Basket", "description": "Colorful woven basket made by local artisans.", "price": 250.00, "image": "b.webp"},
    {"id": 3, "name": "Shea Butter Cream", "description": "Natural moisturizing cream made from organic shea butter.", "price": 180.00, "image": "sb.jpg"},
    {"id": 4, "name": "Kente Cloth", "description": "Traditional Ghanaian Kente cloth, vibrant and authentic.", "price": 450.00, "image": "k.jpg"},
    {"id": 5, "name": "Cocoa Powder", "description": "Pure Ghanaian cocoa powder for baking and drinks.", "price": 100.00, "image": "cp.jpg"},
    {"id": 6, "name": "Dawadawa Spice", "description": "Fermented African locust bean spice used in local cooking.", "price": 90.00, "image": "d.webp"},
]

users = {
    "admin": generate_password_hash("0549070835As")
}

# --- Helper functions ---
def get_product(product_id):
    return next((p for p in products if p["id"] == product_id), None)

def get_cart():
    return session.get("cart", {})

def save_cart(cart):
    session["cart"] = cart

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to continue.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route("/")
@login_required
def home():
    return render_template("home.html", products=products)

@app.route("/product/<int:product_id>")
@login_required
def product(product_id):
    product = get_product(product_id)
    if not product:
        flash("Product not found.")
        return redirect(url_for("home"))
    return render_template("product.html", product=product)

@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    product = get_product(product_id)
    if not product:
        flash("Product not found.")
        return redirect(url_for("home"))

    cart = get_cart()
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    save_cart(cart)
    flash(f"Added {product['name']} to cart.")
    return redirect(request.referrer or url_for("home"))

@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    cart = get_cart()
    cart_items = []
    total = 0.0
    for product_id_str, qty in cart.items():
        product_id = int(product_id_str)
        product = get_product(product_id)
        if product:
            item_total = product["price"] * qty
            total += item_total
            cart_items.append({
                "id": product_id,
                "name": product["name"],
                "description": product["description"],
                "price": product["price"],
                "quantity": qty,
                "image": product["image"],
                "total": item_total
            })

    return render_template("cart.html", cart_items=cart_items, total=total)

@app.route("/update_cart", methods=["POST"])
@login_required
def update_cart():
    cart = {}
    for key, value in request.form.items():
        if key.startswith("quantities[") and key.endswith("]"):
            product_id = key[10:-1]
            try:
                qty = int(value)
                if qty > 0:
                    cart[product_id] = qty
            except:
                pass
    save_cart(cart)
    flash("Cart updated.")
    return redirect(url_for("cart"))

@app.route("/remove_from_cart/<int:product_id>", methods=["POST"])
@login_required
def remove_from_cart(product_id):
    cart = get_cart()
    product_id_str = str(product_id)
    if product_id_str in cart:
        cart.pop(product_id_str)
        save_cart(cart)
        flash("Item removed from cart.")
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    if request.method == "POST":
        name = request.form.get("name")
        address = request.form.get("address")
        card = request.form.get("card")
        expiry = request.form.get("expiry")
        cvv = request.form.get("cvv")
        if not all([name, address, card, expiry, cvv]):
            flash("Please fill in all fields.")
            return redirect(url_for("checkout"))

        session.pop("cart", None)
        flash("Order placed successfully! Thank you for your purchase.")
        return redirect(url_for("home"))
    return render_template("checkout.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users and check_password_hash(users[username], password):
            session["user"] = username
            flash(f"Welcome, {username}!")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out.")
    return redirect(url_for("login"))

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("Username and password required.")
            return redirect(url_for("register"))
        if username in users:
            flash("Username already exists.")
            return redirect(url_for("register"))
        users[username] = generate_password_hash(password)
        flash("Registration successful. Please login.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if session.get("user") != "admin":
        flash("Access denied.")
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        price = request.form.get("price")
        image = request.form.get("image") or "default.jpg"

        if not (name and description and price):
            flash("Please fill all product fields.")
            return redirect(url_for("admin"))

        try:
            price = float(price)
        except ValueError:
            flash("Price must be a number.")
            return redirect(url_for("admin"))

        new_id = max([p["id"] for p in products]) + 1 if products else 1
        products.append({
            "id": new_id,
            "name": name,
            "description": description,
            "price": price,
            "image": image
        })
        flash(f"Product {name} added.")
        return redirect(url_for("admin"))

    return render_template("admin.html")

if __name__ == "__main__":
    app.run(debug=True)
