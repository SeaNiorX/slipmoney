# database.py - SQLite database management for SlipMoney
import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,          -- 'income' or 'expense'
            amount REAL NOT NULL,
            date TEXT NOT NULL,          -- 'YYYY-MM-DD'
            time TEXT NOT NULL,          -- 'HH:MM'
            category TEXT NOT NULL,      -- 'food', 'transportation', etc.
            description TEXT,
            slip_filename TEXT,
            ref_no TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migration if table already existed without ref_no
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN ref_no TEXT")
    except Exception:
        pass

    # Savings Goals (Piggy Banks / กระปุกออมสิน)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS savings_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL NOT NULL DEFAULT 0,
            target_date TEXT,             -- 'YYYY-MM-DD'
            icon TEXT DEFAULT 'piggy-bank',
            color TEXT DEFAULT '#10b981',
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Savings History (Deposits & Withdrawals)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS savings_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            type TEXT NOT NULL,          -- 'deposit' or 'withdraw'
            amount REAL NOT NULL,
            note TEXT,
            date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (goal_id) REFERENCES savings_goals (id) ON DELETE CASCADE
        )
    """)

    # App Settings (for persistent password and configurations)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('app_password', '1234')")

    conn.commit()
    conn.close()

def get_app_password():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_settings WHERE key = 'app_password'")
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else "1234"

def set_app_password(new_password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO app_settings (key, value) VALUES ('app_password', ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (new_password,))
    conn.commit()
    conn.close()

def add_transaction(tx_type, amount, date, time_val, category, description, slip_filename=None, ref_no=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (type, amount, date, time, category, description, slip_filename, ref_no)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_type, float(amount), date, time_val, category, description or "", slip_filename, ref_no.strip() if ref_no else None))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def check_duplicate_ref(ref_no):
    """Check if a reference number already exists in transactions."""
    if not ref_no or not ref_no.strip():
        return None
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM transactions
        WHERE ref_no IS NOT NULL AND ref_no != '' AND UPPER(TRIM(ref_no)) = UPPER(TRIM(?))
        ORDER BY id DESC LIMIT 1
    """, (ref_no.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_transactions(tx_type=None, category=None, month=None, search=None):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []

    if tx_type and tx_type in ['income', 'expense']:
        query += " AND type = ?"
        params.append(tx_type)

    if category and category != 'all':
        query += " AND category = ?"
        params.append(category)

    if month and month != 'all':
        # month formatted as 'YYYY-MM'
        query += " AND strftime('%Y-%m', date) = ?"
        params.append(month)

    if search and search.strip():
        search_kw = f"%{search.strip()}%"
        query += " AND (description LIKE ? OR category LIKE ? OR CAST(amount AS TEXT) LIKE ? OR ref_no LIKE ?)"
        params.extend([search_kw, search_kw, search_kw, search_kw])

    query += " ORDER BY date DESC, time DESC, id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_recent_transactions(limit=5):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM transactions
        ORDER BY date DESC, time DESC, id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_transaction_by_id(tx_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_transaction(tx_id):
    conn = get_db()
    cursor = conn.cursor()
    # Also fetch slip filename to clean up file if desired
    cursor.execute("SELECT slip_filename FROM transactions WHERE id = ?", (tx_id,))
    row = cursor.fetchone()
    slip_file = row['slip_filename'] if row else None

    cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()
    return slip_file

def get_summary_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Total Income
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'income'")
    total_income = cursor.fetchone()[0]
    
    # 2. Total Expense (pure expenses - food, travel, etc., not savings)
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'expense'")
    total_expense = cursor.fetchone()[0]
    
    # 3. Total count
    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_count = cursor.fetchone()[0]

    # 4. Total Saved across all Piggy Banks
    cursor.execute("SELECT COALESCE(SUM(current_amount), 0) FROM savings_goals")
    total_saved = cursor.fetchone()[0]
    
    # Financial metrics
    net_worth = total_income - total_expense
    available_balance = net_worth - total_saved
    conn.close()
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_worth": net_worth,
        "total_saved": total_saved,
        "balance": available_balance,          # Available to spend!
        "available_balance": available_balance,
        "total_count": total_count
    }

def get_chart_data():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Expenses by Category
    cursor.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE type = 'expense'
        GROUP BY category
        ORDER BY total DESC
    """)
    category_rows = cursor.fetchall()
    categories_data = {row['category']: row['total'] for row in category_rows}

    # 2. Monthly Trend (last 6 months)
    cursor.execute("""
        SELECT 
            strftime('%Y-%m', date) as month_key,
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
        FROM transactions
        WHERE date >= date('now', '-6 months')
        GROUP BY month_key
        ORDER BY month_key ASC
    """)
    monthly_rows = cursor.fetchall()
    
    monthly_data = [
        {
            "month": row['month_key'],
            "income": row['income'],
            "expense": row['expense']
        }
        for row in monthly_rows
    ]

    conn.close()
    return {
        "categories": categories_data,
        "monthly": monthly_data
    }

def get_available_months():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT strftime('%Y-%m', date) as m
        FROM transactions
        ORDER BY m DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [row['m'] for row in rows if row['m']]

# ==========================================
# Savings Goals (Piggy Banks / กระปุกออมสิน)
# ==========================================

def create_savings_goal(name, target_amount, current_amount=0.0, target_date=None, icon='piggy-bank', color='#10b981', note=None):
    conn = get_db()
    cursor = conn.cursor()
    init_amt = float(current_amount or 0)
    cursor.execute("""
        INSERT INTO savings_goals (name, target_amount, current_amount, target_date, icon, color, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name.strip(), float(target_amount), init_amt, target_date or None, icon or 'piggy-bank', color or '#10b981', note or ''))
    conn.commit()
    new_id = cursor.lastrowid
    
    # Record initial deposit if any in savings history (no expense transaction created)
    if init_amt > 0:
        today_str = datetime.date.today().strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO savings_history (goal_id, type, amount, note, date)
            VALUES (?, 'deposit', ?, 'เงินเริ่มต้น / Initial balance', ?)
        """, (new_id, init_amt, today_str))
        conn.commit()

    conn.close()
    return new_id

def get_savings_goals():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM savings_goals
        ORDER BY (current_amount >= target_amount) ASC, id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    goals = []
    for r in rows:
        d = dict(r)
        target = d['target_amount']
        current = d['current_amount']
        percent = round((current / target * 100), 1) if target > 0 else 0
        d['percent'] = min(percent, 100.0)
        d['is_completed'] = current >= target
        d['remaining'] = max(0.0, target - current)
        goals.append(d)
    return goals

def get_savings_goal_by_id(goal_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM savings_goals WHERE id = ?", (goal_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    target = d['target_amount']
    current = d['current_amount']
    d['percent'] = min(round((current / target * 100), 1), 100.0) if target > 0 else 0
    d['is_completed'] = current >= target
    d['remaining'] = max(0.0, target - current)
    return d

def deposit_to_savings(goal_id, amount, note=None, date=None):
    """Add funds into a piggy bank and log history (does NOT count as expense)."""
    conn = get_db()
    cursor = conn.cursor()
    amt = float(amount)
    if amt <= 0:
        conn.close()
        return False

    cursor.execute("SELECT name FROM savings_goals WHERE id = ?", (goal_id,))
    goal = cursor.fetchone()
    if not goal:
        conn.close()
        return False

    cursor.execute("UPDATE savings_goals SET current_amount = current_amount + ? WHERE id = ?", (amt, goal_id))
    
    tx_date = date or datetime.date.today().strftime('%Y-%m-%d')

    cursor.execute("""
        INSERT INTO savings_history (goal_id, type, amount, note, date)
        VALUES (?, 'deposit', ?, ?, ?)
    """, (goal_id, amt, note or '', tx_date))

    conn.commit()
    conn.close()
    return True

def withdraw_from_savings(goal_id, amount, note=None, date=None):
    """Withdraw funds from a piggy bank and log history (does NOT count as income)."""
    conn = get_db()
    cursor = conn.cursor()
    amt = float(amount)
    if amt <= 0:
        conn.close()
        return False

    cursor.execute("SELECT name, current_amount FROM savings_goals WHERE id = ?", (goal_id,))
    goal = cursor.fetchone()
    if not goal:
        conn.close()
        return False

    new_amount = max(0.0, goal['current_amount'] - amt)
    actual_deducted = goal['current_amount'] - new_amount
    if actual_deducted <= 0:
        conn.close()
        return False

    cursor.execute("UPDATE savings_goals SET current_amount = ? WHERE id = ?", (new_amount, goal_id))
    
    tx_date = date or datetime.date.today().strftime('%Y-%m-%d')

    cursor.execute("""
        INSERT INTO savings_history (goal_id, type, amount, note, date)
        VALUES (?, 'withdraw', ?, ?, ?)
    """, (goal_id, actual_deducted, note or '', tx_date))

    conn.commit()
    conn.close()
    return True

def delete_savings_goal(goal_id):
    """Delete a piggy bank. Any saved money automatically returns to available balance without needing transaction records."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM savings_history WHERE goal_id = ?", (goal_id,))
    cursor.execute("DELETE FROM savings_goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()
    return True

def get_savings_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COALESCE(SUM(current_amount), 0) as total_saved,
            COALESCE(SUM(target_amount), 0) as total_target,
            COUNT(*) as total_goals,
            SUM(CASE WHEN current_amount >= target_amount THEN 1 ELSE 0 END) as completed_goals
        FROM savings_goals
    """)
    row = cursor.fetchone()
    conn.close()
    
    total_saved = row['total_saved'] or 0.0
    total_target = row['total_target'] or 0.0
    overall_percent = round((total_saved / total_target * 100), 1) if total_target > 0 else 0
    
    return {
        "total_saved": total_saved,
        "total_target": total_target,
        "total_goals": row['total_goals'] or 0,
        "completed_goals": row['completed_goals'] or 0,
        "active_goals": (row['total_goals'] or 0) - (row['completed_goals'] or 0),
        "overall_percent": min(overall_percent, 100.0)
    }

def get_savings_history(goal_id=None, limit=15):
    conn = get_db()
    cursor = conn.cursor()
    if goal_id:
        cursor.execute("""
            SELECT h.*, g.name as goal_name, g.color, g.icon
            FROM savings_history h
            JOIN savings_goals g ON h.goal_id = g.id
            WHERE h.goal_id = ?
            ORDER BY h.date DESC, h.id DESC
            LIMIT ?
        """, (goal_id, limit))
    else:
        cursor.execute("""
            SELECT h.*, g.name as goal_name, g.color, g.icon
            FROM savings_history h
            JOIN savings_goals g ON h.goal_id = g.id
            ORDER BY h.date DESC, h.id DESC
            LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
