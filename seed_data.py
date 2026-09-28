# seed_data.py - Seed realistic initial data and sample slips
import os
import database
from PIL import Image, ImageDraw, ImageFont

def create_sample_slip(filename, amount_str, date_str, time_str, sender, receiver):
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    filepath = os.path.join(uploads_dir, filename)
    
    # Generate a clean slip image
    width, height = 480, 680
    img = Image.new("RGB", (width, height), color="#f8fafc")
    draw = ImageDraw.Draw(img)

    # Top header bar (Green for K-PLUS style or Purple/Blue)
    draw.rectangle([(0, 0), (width, 100)], fill="#059669")
    draw.rectangle([(0, 95), (width, 100)], fill="#047857")

    # Header text
    draw.text((30, 35), "โอนเงินสำเร็จ / Transfer Successful", fill="#ffffff")

    # Body Card
    draw.rectangle([(25, 120), (width - 25, height - 30)], fill="#ffffff", outline="#e2e8f0", width=2)

    # Content
    y = 150
    # Amount
    draw.text((45, y), "จำนวนเงิน / Amount", fill="#64748b")
    draw.text((45, y + 25), f"฿{amount_str}", fill="#0f172a")
    
    y += 85
    draw.line([(45, y), (width - 45, y)], fill="#f1f5f9", width=1)
    
    y += 20
    draw.text((45, y), "จาก / From:", fill="#64748b")
    draw.text((45, y + 22), sender, fill="#0f172a")

    y += 65
    draw.text((45, y), "ไปยัง / To:", fill="#64748b")
    draw.text((45, y + 22), receiver, fill="#0f172a")

    y += 65
    draw.line([(45, y), (width - 45, y)], fill="#f1f5f9", width=1)

    y += 20
    draw.text((45, y), "วันที่-เวลา / Date & Time", fill="#64748b")
    draw.text((45, y + 22), f"{date_str} {time_str}", fill="#0f172a")

    y += 65
    draw.text((45, y), "เลขที่รายการ / Ref No.", fill="#64748b")
    draw.text((45, y + 22), "20260928784930129", fill="#64748b")

    # Bottom watermark
    draw.text((width // 2 - 60, height - 60), "SlipMoney Bank", fill="#cbd5e1")

    img.save(filepath, format="JPEG", quality=90)
    print(f"Created sample slip: {filepath}")
    return filename

def seed():
    database.init_db()
    
    # Check if data already exists
    txs = database.get_transactions()
    if len(txs) > 0:
        print(f"Database already has {len(txs)} transactions.")
        return

    # Create sample slip files
    slip1 = create_sample_slip("sample_slip_coffee.jpg", "250.00", "28/09/2026", "14:32", "นาย สมชาย มะลิ", "ร้านกาแฟสุขใจ")
    slip2 = create_sample_slip("sample_slip_dinner.jpg", "1,250.00", "27/09/2026", "19:15", "นาย สมชาย มะลิ", "ร้านอาหารริมน้ำ")

    # Add realistic transactions
    data = [
        ("income", 25000.00, "2026-09-01", "09:00", "salary", "เงินเดือนประจำเดือนกันยายน", None),
        ("expense", 3500.00, "2026-09-05", "10:30", "household", "ค่าเช่าห้องพักและค่าน้ำไฟ", None),
        ("expense", 1250.00, "2026-09-27", "19:15", "food", "ทานอาหารค่ำกับครอบครัว", slip2),
        ("expense", 250.00, "2026-09-28", "14:32", "food", "กาแฟและของว่างยามบ่าย", slip1),
        ("expense", 180.00, "2026-09-28", "08:15", "transportation", "ค่ารถไฟฟ้า BTS", None),
        ("expense", 890.00, "2026-09-25", "15:40", "shopping", "ซื้อของใช้ส่วนตัวออนไลน์", None),
        ("expense", 450.00, "2026-09-20", "20:00", "entertainment", "ตั๋วชมภาพยนตร์", None),
    ]

    for tx_type, amount, date, time_val, cat, desc, slip in data:
        database.add_transaction(tx_type, amount, date, time_val, cat, desc, slip)

    print("Successfully seeded initial transactions!")

if __name__ == "__main__":
    seed()
