# app.py - SlipMoney Backend Application
import os
import uuid
import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, send_from_directory
)
from werkzeug.utils import secure_filename
from translations import get_translation_dict, CATEGORIES, TRANSLATIONS, SAVINGS_ICONS, SAVINGS_COLORS
import database
import ocr_service

app = Flask(__name__)
app.secret_key = "slipmoney-super-secret-key-2026-cmu"

# 1. Simple Single Password Configuration
PASSWORD = "1234"

# Upload Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024 # 16 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
database.init_db()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Context processor for templates: inject translations & current language
@app.context_processor
def inject_global_data():
    lang = session.get("lang", "th")
    t = get_translation_dict(lang)
    return {
        "t": t,
        "current_lang": lang,
        "categories": CATEGORIES,
        "savings_icons": SAVINGS_ICONS,
        "savings_colors": SAVINGS_COLORS,
        "all_langs": ["th", "en"]
    }

# Helper filter for currency formatting
@app.template_filter("currency")
def currency_filter(value):
    try:
        val = float(value)
        return f"{val:,.2f}"
    except (ValueError, TypeError):
        return "0.00"

# Category name helper
@app.template_filter("cat_name")
def cat_name_filter(cat_val):
    lang = session.get("lang", "th")
    t = get_translation_dict(lang)
    for cat in CATEGORIES:
        if cat["val"] == cat_val:
            return t.get(cat["key"], cat_val)
    return cat_val

# Auth decorator/helper
def is_logged_in():
    return session.get("logged_in") is True

@app.before_request
def check_authentication():
    # Public endpoints
    allowed_routes = ["login", "set_language", "static", "uploaded_file"]
    endpoint = request.endpoint
    if endpoint and endpoint in allowed_routes:
        return None
    
    # If not logged in and requesting protected page, redirect to login
    if not is_logged_in():
        return redirect(url_for("login"))

# Routes
@app.route("/")
def index():
    if is_logged_in():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/set-language/<lang>")
def set_language(lang):
    if lang in TRANSLATIONS:
        session["lang"] = lang
    # Redirect back to referring page or dashboard
    ref = request.referrer
    if ref and "/set-language/" not in ref:
        return redirect(ref)
    return redirect(url_for("dashboard"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if is_logged_in():
        return redirect(url_for("dashboard"))

    error_msg = None
    lang = session.get("lang", "th")
    t = get_translation_dict(lang)

    if request.method == "POST":
        password = request.form.get("password", "")
        current_password = database.get_app_password()
        if password == current_password:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            error_msg = t.get("invalid_password")

    return render_template("login.html", error=error_msg)

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    error_msg = None
    lang = session.get("lang", "th")
    t = get_translation_dict(lang)

    if request.method == "POST":
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not new_password:
            error_msg = t.get("password_empty")
        elif new_password != confirm_password:
            error_msg = t.get("password_mismatch")
        else:
            database.set_app_password(new_password)
            flash(t.get("password_reset_success"), "success")
            session.pop("logged_in", None)
            return redirect(url_for("login"))

    return render_template("reset_password.html", error=error_msg)

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    stats = database.get_summary_stats()
    recent = database.get_recent_transactions(limit=6)
    chart_info = database.get_chart_data()
    savings_stats = database.get_savings_stats()
    top_savings_goals = database.get_savings_goals()[:3]

    # Prepare translated category names for the chart
    lang = session.get("lang", "th")
    t = get_translation_dict(lang)
    
    category_chart_labels = []
    category_chart_values = []
    for cat_val, amount in chart_info["categories"].items():
        # Find translated label
        label = cat_val
        for c in CATEGORIES:
            if c["val"] == cat_val:
                label = t.get(c["key"], cat_val)
                break
        category_chart_labels.append(label)
        category_chart_values.append(amount)

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_transactions=recent,
        category_chart_labels=category_chart_labels,
        category_chart_values=category_chart_values,
        monthly_chart_data=chart_info["monthly"],
        savings_stats=savings_stats,
        top_savings_goals=top_savings_goals
    )

@app.route("/transactions")
def transactions():
    filter_type = request.args.get("type", "all")
    filter_category = request.args.get("category", "all")
    filter_month = request.args.get("month", "all")
    search = request.args.get("search", "")

    all_txs = database.get_transactions(
        tx_type=filter_type if filter_type != "all" else None,
        category=filter_category if filter_category != "all" else None,
        month=filter_month if filter_month != "all" else None,
        search=search if search else None
    )

    available_months = database.get_available_months()

    return render_template(
        "transactions.html",
        transactions=all_txs,
        filter_type=filter_type,
        filter_category=filter_category,
        filter_month=filter_month,
        search=search,
        available_months=available_months
    )

@app.route("/add-transaction", methods=["GET", "POST"])
def add_transaction():
    lang = session.get("lang", "th")
    t = get_translation_dict(lang)

    if request.method == "POST":
        tx_type = request.form.get("type", "expense")
        amount = request.form.get("amount", "").strip()
        date = request.form.get("date", "").strip()
        time_val = request.form.get("time", "").strip()
        category = request.form.get("category", "other").strip()
        description = request.form.get("description", "").strip()
        slip_filename = request.form.get("slip_filename", "").strip()
        ref_no = request.form.get("ref_no", "").strip() or None

        # Prevent duplicate slip submission by ref_no
        if ref_no:
            existing_dup = database.check_duplicate_ref(ref_no)
            if existing_dup:
                err_msg = t.get("duplicate_slip_error", "สลิปนี้ซ้ำ").format(ref_no=ref_no)
                flash(err_msg, "error")
                return redirect(url_for("add_transaction"))

        # Handle file upload directly from form if not pre-uploaded via OCR AJAX
        file = request.files.get("slip_file")
        if file and file.filename != "" and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            slip_filename = f"slip_{uuid.uuid4().hex[:12]}.{ext}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], slip_filename)
            file.save(filepath)

        if not amount:
            flash(t.get("fill_required"), "error")
            return redirect(url_for("add_transaction"))

        try:
            amt_float = float(amount.replace(",", ""))
        except ValueError:
            flash(t.get("fill_required"), "error")
            return redirect(url_for("add_transaction"))

        if not date:
            date = datetime.date.today().strftime("%Y-%m-%d")
        if not time_val:
            time_val = datetime.datetime.now().strftime("%H:%M")

        database.add_transaction(
            tx_type=tx_type,
            amount=amt_float,
            date=date,
            time_val=time_val,
            category=category,
            description=description,
            slip_filename=slip_filename if slip_filename else None,
            ref_no=ref_no
        )

        flash(t.get("transaction_added"), "success")
        return redirect(url_for("transactions"))

    # Default values for GET form
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    now_time = datetime.datetime.now().strftime("%H:%M")
    return render_template("add_transaction.html", default_date=today_str, default_time=now_time)

@app.route("/api/ocr-slip", methods=["POST"])
def api_ocr_slip():
    """
    Endpoint for uploading a slip image and performing OCR on-the-fly.
    Extracts amount, date, time, ref_no and returns JSON to auto-fill form.
    Checks for duplicate slip reference number in database.
    """
    if "slip" not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"}), 400

    file = request.files["slip"]
    if file.filename == "":
        return jsonify({"success": False, "message": "Empty filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "message": "Invalid file type. Supports JPG, JPEG, PNG"}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_filename = f"slip_{uuid.uuid4().hex[:12]}.{ext}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
    file.save(filepath)

    # Perform OCR
    ocr_result = ocr_service.process_slip(filepath)
    ocr_result["filename"] = unique_filename
    ocr_result["file_url"] = url_for("uploaded_file", filename=unique_filename)

    # Check for duplicate slip by reference number
    ref_no = ocr_result.get("ref_no")
    if ref_no:
        duplicate = database.check_duplicate_ref(ref_no)
        if duplicate:
            ocr_result["is_duplicate"] = True
            ocr_result["duplicate_info"] = {
                "id": duplicate["id"],
                "amount": f"{duplicate['amount']:.2f}",
                "date": duplicate["date"],
                "time": duplicate["time"],
                "category": duplicate["category"],
                "ref_no": duplicate.get("ref_no")
            }
        else:
            ocr_result["is_duplicate"] = False
    else:
        ocr_result["is_duplicate"] = False

    return jsonify(ocr_result)

# ==========================================
# Savings Goals (Piggy Banks / กระปุกออมสิน)
# ==========================================

@app.route("/savings")
def savings():
    goals = database.get_savings_goals()
    stats = database.get_savings_stats()
    main_stats = database.get_summary_stats()
    history = database.get_savings_history(limit=15)
    return render_template(
        "savings.html",
        goals=goals,
        stats=stats,
        history=history,
        main_balance=main_stats["balance"],
        savings_icons=SAVINGS_ICONS,
        savings_colors=SAVINGS_COLORS
    )

@app.route("/api/savings/create", methods=["POST"])
def api_savings_create():
    lang = session.get("lang", "th")
    t = get_translation_dict(lang)
    
    name = request.form.get("name", "").strip()
    target_amount = request.form.get("target_amount", "").strip()
    initial_amount = request.form.get("current_amount", "0").strip() or "0"
    target_date = request.form.get("target_date", "").strip() or None
    icon = request.form.get("icon", "piggy-bank").strip()
    color = request.form.get("color", "#10b981").strip()
    note = request.form.get("note", "").strip()

    if not name or not target_amount:
        flash(t.get("fill_required"), "error")
        return redirect(url_for("savings"))

    try:
        target_val = float(target_amount.replace(",", ""))
        init_val = float(initial_amount.replace(",", ""))
        if target_val <= 0 or init_val < 0:
            flash(t.get("invalid_amount"), "error")
            return redirect(url_for("savings"))
    except ValueError:
        flash(t.get("invalid_amount"), "error")
        return redirect(url_for("savings"))

    # Check if wallet balance is sufficient for initial deposit
    if init_val > 0:
        main_stats = database.get_summary_stats()
        if init_val > main_stats["balance"]:
            flash(t.get("insufficient_main_balance", "ยอดเงินคงเหลือไม่เพียงพอ").format(balance=f"{main_stats['balance']:,.2f}"), "error")
            return redirect(url_for("savings"))

    database.create_savings_goal(
        name=name,
        target_amount=target_val,
        current_amount=init_val,
        target_date=target_date,
        icon=icon,
        color=color,
        note=note
    )
    flash(t.get("goal_created_success"), "success")
    return redirect(url_for("savings"))

@app.route("/api/savings/deposit", methods=["POST"])
def api_savings_deposit():
    lang = session.get("lang", "th")
    t = get_translation_dict(lang)

    goal_id = request.form.get("goal_id")
    amount = request.form.get("amount", "").strip()
    note = request.form.get("note", "").strip()
    date_val = request.form.get("date", "").strip() or datetime.date.today().strftime("%Y-%m-%d")

    try:
        amt_val = float(amount.replace(",", ""))
        if amt_val <= 0:
            flash(t.get("invalid_amount"), "error")
            return redirect(url_for("savings"))
    except (ValueError, TypeError):
        flash(t.get("invalid_amount"), "error")
        return redirect(url_for("savings"))

    # Check if wallet balance is sufficient
    main_stats = database.get_summary_stats()
    if amt_val > main_stats["balance"]:
        flash(t.get("insufficient_main_balance", "ยอดเงินคงเหลือไม่เพียงพอ").format(balance=f"{main_stats['balance']:,.2f}"), "error")
        return redirect(url_for("savings"))

    success = database.deposit_to_savings(goal_id, amt_val, note=note, date=date_val)
    if success:
        flash(t.get("deposit_success"), "success")
    else:
        flash(t.get("invalid_amount"), "error")
    return redirect(url_for("savings"))

@app.route("/api/savings/withdraw", methods=["POST"])
def api_savings_withdraw():
    lang = session.get("lang", "th")
    t = get_translation_dict(lang)

    goal_id = request.form.get("goal_id")
    amount = request.form.get("amount", "").strip()
    note = request.form.get("note", "").strip()
    date_val = request.form.get("date", "").strip() or datetime.date.today().strftime("%Y-%m-%d")

    try:
        amt_val = float(amount.replace(",", ""))
        if amt_val <= 0:
            flash(t.get("invalid_amount"), "error")
            return redirect(url_for("savings"))
    except (ValueError, TypeError):
        flash(t.get("invalid_amount"), "error")
        return redirect(url_for("savings"))

    success = database.withdraw_from_savings(goal_id, amt_val, note=note, date=date_val)
    if success:
        flash(t.get("withdraw_success"), "success")
    else:
        flash(t.get("insufficient_savings"), "error")
    return redirect(url_for("savings"))

@app.route("/api/savings/delete/<int:goal_id>", methods=["POST"])
def api_savings_delete(goal_id):
    lang = session.get("lang", "th")
    t = get_translation_dict(lang)
    database.delete_savings_goal(goal_id)
    flash(t.get("goal_deleted_success"), "success")
    return redirect(url_for("savings"))

@app.route("/api/delete-transaction/<int:tx_id>", methods=["POST"])
def delete_transaction(tx_id):
    slip_file = database.delete_transaction(tx_id)
    if slip_file:
        try:
            slip_path = os.path.join(app.config["UPLOAD_FOLDER"], slip_file)
            if os.path.exists(slip_path):
                os.remove(slip_path)
        except Exception as e:
            print(f"Error removing slip file: {e}")

    # Check if request wants JSON or redirect
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True})
    
    lang = session.get("lang", "th")
    t = get_translation_dict(lang)
    flash(t.get("transaction_deleted"), "success")
    return redirect(request.referrer or url_for("transactions"))

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
