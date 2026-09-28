# SlipMoney 💸
**ระบบเว็บแอปพลิเคชันบันทึกรายรับ-รายจ่าย อัจฉริยะด้วย OCR อ่านสลิปธนาคาร**  
*(Smart Income & Expense Tracker with Slip OCR & Full Bilingual Support)*

---

## 🌟 ฟีเจอร์เด่น (Key Features)

### 1. ระบบเข้าสู่ระบบแบบเรียบง่าย (Simple Login)
* ใช้รหัสผ่านเดียว **`1234`** กำหนดใน Python Backend (`PASSWORD = "1234"`)
* ตรวจสอบด้วย `if password == PASSWORD` โดยตรง
* ไม่ต้องสมัครสมาชิก ไม่ต้องมีตาราง User ในฐานข้อมูล
* จัดการสถานะการเข้าสู่ระบบผ่าน **Flask Session**
* มีระบบป้องกันหน้า Dashboard / Transactions / Add Transaction หากยังไม่ได้เข้าสู่ระบบ
* ปุ่มออกจากระบบ (Logout) ใน Navbar และ Mobile Drawer

### 2. ระบบ 2 ภาษาแท้จริง (100% Bilingual Thai 🇹🇭 & English EN)
* สลับภาษาได้ทันทีผ่าน Navbar: `🇹🇭 ไทย | EN English`
* ระบบแปลภาษาถูกแยกเป็นสัดส่วนชัดเจนใน `translations.py`
* ไม่มีข้อความ hard-code ใน HTML Template
* มีระบบ Fallback เป็นภาษาอังกฤษอัตโนมัติหากไม่พบคีย์
* จดจำภาษาที่เลือกไว้ใน Flask Session แม้เปลี่ยนหน้าหรือเข้าใหม่ภาษาก็ยังคงเดิม
* หมวดหมู่, วันที่, ปุ่ม, แบบฟอร์ม, กราฟ, ข้อความแจ้งเตือน, และหน้าต่าง Modal แปลภาษาครบถ้วน 100%

### 3. ระบบอ่านสลิปธนาคารด้วย OCR (Slip OCR Auto-Fill)
* รองรับไฟล์ภาพสลิป: **JPG, JPEG, PNG**
* ใช้ **Tesseract OCR (ภาษาไทย `tha` + ภาษาอังกฤษ `eng`)** พร้อมระบบ Image Preprocessing
* อ่านและดึงข้อมูลสำคัญอัตโนมัติ:
  * **จำนวนเงิน (Amount):** ตรวจจับตัวเลขทศนิยม 2 ตำแหน่ง, สัญลักษณ์ ฿, บาท, THB
  * **วันที่ (Date):** ตรวจจับ วัน/เดือน/ปี ทั้งแบบ ค.ศ. (CE) และ พ.ศ. (BE) พร้อมแปลงเป็น ISO YYYY-MM-DD
  * **เวลา (Time):** ตรวจจับชั่วโมงและนาที HH:MM (24 ชั่วโมง)
* นำข้อมูลที่อ่านได้กรอกลงในฟอร์มให้อัตโนมัติ (Auto-fill) ทันทีที่อัปโหลด
* ผู้ใช้สามารถตรวจสอบและแก้ไขข้อมูลก่อนกดบันทึกได้ตลอดเวลา
* หาก OCR ไม่พบจำนวนเงิน จะเว้นว่างไว้ให้ผู้ใช้ระบุเอง

### 4. แดชบอร์ดสรุปผลการเงิน (Financial Dashboard)
* **Summary Cards:** รายรับทั้งหมด (Total Income), รายจ่ายทั้งหมด (Total Expenses), ยอดคงเหลือ (Balance), จำนวนรายการ (Transactions)
* **Interactive Charts (Chart.js):**
  * กราฟแท่งเปรียบเทียบแนวโน้ม รายรับ vs รายจ่าย (Monthly Trend)
  * กราฟวงกลมแจกแจงค่าใช้จ่ายตามหมวดหมู่ (Expenses by Category)
* **รายการล่าสุด (Recent Transactions):** แสดง 6 รายการล่าสุด พร้อมปุ่มเปิดดูรูปสลิป

### 5. หน้ารายการทั้งหมด (All Transactions Management)
* ค้นหาข้อความ / รายละเอียด / จำนวนเงิน (Instant Search)
* กรองตามประเภท (รายรับ / รายจ่าย / ทั้งหมด)
* กรองตามหมวดหมู่ (อาหาร, เดินทาง, ช้อปปิ้ง, ค่าใช้จ่ายบ้าน, บันเทิง, เงินเดือน, อื่น ๆ)
* กรองตามเดือน (Filter by Month)
* ดูรายละเอียดรายการเต็ม (Transaction Details Modal)
* ดูรูปภาพสลิปขนาดใหญ่ (Slip Preview Modal)
* ลบรายการพร้อมหน้าต่างยืนยัน (Delete Confirmation Modal)

### 6. ฐานข้อมูล SQLite (`database.db`)
* ตาราง `transactions`:
  * `id`: รหัสรายการ (Auto Increment)
  * `type`: ชนิดรายการ (`income` หรือ `expense`)
  * `amount`: จำนวนเงิน
  * `date`: วันที่ (YYYY-MM-DD)
  * `time`: เวลา (HH:MM)
  * `category`: หมวดหมู่มาตรฐาน
  * `description`: รายละเอียดหรือบันทึกช่วยจำ
  * `slip_filename`: ชื่อไฟล์สลิปที่เก็บในโฟลเดอร์ `uploads/`
  * `created_at`: วันที่และเวลาที่บันทึกข้อมูล

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
slipmoney/
├── app.py                     # Flask Application & Routing
├── database.py                # SQLite Database Helper Functions
├── database.db                # SQLite Database File
├── ocr_service.py             # OCR Slip Processing Engine (pytesseract)
├── translations.py            # Bilingual Dictionary (Thai / English)
├── requirements.txt           # Python Dependencies
├── seed_data.py               # Data Seeder with Sample Slips
├── test_app.py                # Automated Test Suite (7 Unit Tests)
├── verify_translations.py     # Bilingual Verification Script
├── tessdata/                  # Tesseract Language Models (eng + tha)
│   ├── eng.traineddata
│   └── tha.traineddata
├── uploads/                   # Uploaded slip images storage
├── templates/                 # Jinja2 HTML Templates
│   ├── base.html              # Base layout with navbar & modals
│   ├── login.html             # Login page
│   ├── dashboard.html         # Dashboard with metrics & charts
│   ├── add_transaction.html   # Add transaction form with OCR dropzone
│   └── transactions.html      # Transactions table with filters
└── static/
    ├── css/
    │   └── style.css          # Modern Fintech UI styling
    └── js/
        ├── script.js          # Global app functions & modal handling
        ├── dashboard-charts.js# Chart.js visualization
        ├── add-transaction.js # OCR upload and auto-fill logic
        └── transactions.js    # Transactions table modals
```

---

## 🚀 วิธีการติดตั้งและรันโปรเจกต์ (Installation & Quickstart)

### 1. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

*(หมายเหตุ: ระบบมาพร้อมกับ `tessdata` ภาษาไทยและอังกฤษในตัวโปรเจกต์แล้ว)*

### 2. เตรียมข้อมูลทดสอบ (Optional)
หากต้องการใส่ข้อมูลตัวอย่างและรูปสลิปจำลองสำหรับทดสอบ:
```bash
python seed_data.py
```

### 3. รันเว็บแอปพลิเคชัน
```bash
python app.py
```

เปิดเบราว์เซอร์ไปที่:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### 4. การเข้าสู่ระบบ
* **รหัสผ่าน (Password):** `1234`

---

## 🧪 การรันชุดทดสอบ (Running Tests)

ทดสอบระบบการทำงานและฟังก์ชันทั้งหมด:
```bash
python test_app.py
```

ทดสอบการแปลภาษา 2 ภาษา (Bilingual Verification):
```bash
python verify_translations.py
```
