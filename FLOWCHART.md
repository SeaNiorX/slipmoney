# SlipMoney 💸 - Flowcharts & System Architecture

เอกสารผังงาน (Flowchart) ของระบบ **SlipMoney** จำลองและอ้างอิงตรงกับ **Python Source Code จริง** ของโปรเจกต์ แสดง Input → Process → Output, Decision Structure (`if`), และ Repetition Structure (`for` loop) ครบถ้วนตามข้อกำหนด

---

## 1. Flowchart: ระบบตรวจสอบสิทธิ์การเข้าสู่ระบบ (Authentication & Route Guard)
อ้างอิงโค้ดจริงจาก [`app.py`](file:///c:/Users/Ghost%20Spectre/Documents/CMU/954142/Project/app.py) บรรทัดที่ 70–136 (`check_authentication`, `login`)

```mermaid
flowchart TD
    Start([เริ่มต้น / User Request URL]) --> CheckPublic{"Request Endpoint อยู่ใน<br>allowed_routes หรือไม่?<br>(login, static, etc.)"}
    
    CheckPublic -- ใช่ (True) --> ProcessRequest[อนุญาตให้เข้าถึงหน้านั้นๆ]
    CheckPublic -- ไม่ใช่ (False) --> CheckSession{"session['logged_in'] == True<br>เข้าสู่ระบบแล้วหรือไม่?"}
    
    CheckSession -- ใช่ (True) --> ProcessRequest
    CheckSession -- ไม่ใช่ (False) --> RedirectLogin["Redirect ไปที่หน้า /login"]
    
    RedirectLogin --> InputPassword[/"ผู้ใช้กรอกรหัสผ่าน (password)"/]
    InputPassword --> CheckPass{"password == current_password?<br>(รหัสถูกต้องหรือไม่?)"}
    
    CheckPass -- ใช่ (True) --> SetSession["กำหนด session['logged_in'] = True<br>และ Redirect ไปยัง /dashboard"]
    SetSession --> ShowDashboard[/"แสดงผลหน้า Financial Dashboard"/]
    
    CheckPass -- ไม่ใช่ (False) --> FlashError["แสดง Flash Message แจ้งรหัสผ่านไม่ถูกต้อง"]
    FlashError --> InputPassword
    
    ShowDashboard --> End([สิ้นสุด])
    ProcessRequest --> End
```

---

## 2. Flowchart: ระบบอ่านสลิปธนาคารด้วย OCR (Slip OCR Auto-Fill Engine)
อ้างอิงโค้ดจริงจาก [`ocr_service.py`](file:///c:/Users/Ghost%20Spectre/Documents/CMU/954142/Project/ocr_service.py) บรรทัดที่ 48–355 และ [`app.py`](file:///c:/Users/Ghost%20Spectre/Documents/CMU/954142/Project/app.py) บรรทัดที่ 271–337 (`api_ocr_slip`)

```mermaid
flowchart TD
    StartOCR([เริ่มต้น: ผู้ใช้อัปโหลดรูปสลิป]) --> InputImage[/"รับไฟล์ภาพสลิป (JPG, PNG)"/]
    InputImage --> CheckExt{"นามสกุลไฟล์ถูกต้องหรือไม่?<br>(jpg, jpeg, png)"}
    
    CheckExt -- ไม่ถูกต้อง --> ErrFile[/"ส่ง JSON: Invalid file type"/]
    CheckExt -- ถูกต้อง --> Preprocess["Image Preprocessing:<br>1. แปลง EXIF Orientation<br>2. แปลงเป็น Grayscale"]
    
    Preprocess --> CheckWidth{"ตรวจสอบขนาดภาพ (Width)"}
    CheckWidth -- "width > 750" --> Downscale["ปรับลดขนาดลงเหลือ 750px"]
    CheckWidth -- "width < 550" --> Upscale["ปรับขยายขนาดขึ้นเป็น 650px"]
    CheckWidth -- "550 <= width <= 750" --> KeepSize["คงขนาดเดิมไว้"]
    
    Downscale --> Contrast["Contrast Enhancement (1.4x)"]
    Upscale --> Contrast
    KeepSize --> Contrast
    
    Contrast --> RunTesseract["ประมวลผล OCR ด้วย pytesseract<br>(lang = tha + eng)"]
    RunTesseract --> ExtractTokens[/"ได้ข้อความดิบ (raw text)"/]
    
    ExtractTokens --> LoopAmount["Loop คัดกรองตัวเลขทศนิยม (parse_amount)<br>ตรวจสอบเงื่อนไข: 0.50 <= val <= 10,000,000"]
    LoopAmount --> LoopDate["Loop ค้นหาวันที่ (parse_date)<br>Nested Loop จับคู่เดือนใน MONTH_GROUPS<br>Selection Structure ปรับปี พ.ศ. / ค.ศ."]
    LoopDate --> ParseTime["ดึงเวลาทำรายการ HH:MM (parse_time)"]
    ParseTime --> ParseRef["ดึงรหัสอ้างอิงธนาคาร (parse_ref_no)"]
    
    ParseRef --> CheckRef{"ตรวจพบ Ref No. หรือไม่?"}
    CheckRef -- ใช่ --> CheckDup{"Query SQLite: รหัสนี้มีใน DB แล้วหรือไม่?<br>(database.find_duplicate_slip)"}
    CheckRef -- ไม่ใช่ --> BuildJSON["สร้างผลลัพธ์ JSON"]
    
    CheckDup -- พบสลิปซ้ำ --> FlagDup["กำหนด is_duplicate = True<br>แจ้งเตือนสลิปเคยบันทึกแล้ว"]
    CheckDup -- ไม่ซ้ำ --> BuildJSON
    FlagDup --> BuildJSON
    
    BuildJSON --> ReturnJSON[/"ส่ง JSON Response กลับไปยังเบราว์เซอร์<br>(amount, date, time, ref_no)"/]
    ReturnJSON --> AutoFill["JavaScript กรอกข้อมูลลงแบบฟอร์มอัตโนมัติ"]
    AutoFill --> EndOCR([สิ้นสุด])
    ErrFile --> EndOCR
```

---

## 3. Flowchart: ระบบประมวลผล 2D Nested List (Category Financial Matrix)
อ้างอิงโค้ดจริงจาก [`database.py`](file:///c:/Users/Ghost%20Spectre/Documents/CMU/954142/Project/database.py) บรรทัดที่ 465–550 (`get_financial_summary_matrix`, `process_matrix_summary`)

```mermaid
flowchart TD
    StartMatrix([เริ่มต้น: คำนวณสรุปสถิติการเงิน]) --> QueryDB["SQL Query: GROUP BY category<br>คำนวณ SUM(income), SUM(expense), COUNT(id)"]
    QueryDB --> InitList["กำหนดตัวแปร matrix = []<br>(Outer List ว่าง)"]
    
    InitList --> LoopRow{"วนลูปสำหรับแต่ละแถวใน SQL Results<br>(for r in rows)"}
    
    LoopRow -- ยังมีข้อมูลแถวถัดไป --> CreateInner["สร้าง Inner List:<br>row = [category, income, expense, net, count]"]
    CreateInner --> AppendRow["matrix.append(row)<br>(ประกอบเป็น 2D Nested List)"]
    AppendRow --> LoopRow
    
    LoopRow -- ครบทุกแถวแล้ว --> ReturnMatrix[/"ได้ตัวแปร 2D Nested List: matrix"/]
    
    ReturnMatrix --> ProcessStart["เริ่มต้นประมวลผล: process_matrix_summary(matrix)<br>กำหนด total_inc=0, total_exp=0, active_categories=0"]
    
    ProcessStart --> LoopMatrix{"วนลูปอ่านแต่ละแถวใน matrix<br>(for row in matrix)"}
    
    LoopMatrix -- ยังมีแถวถัดไป --> AccessElements["เข้าถึงข้อมูลผ่าน Index:<br>cat = row[0]<br>inc = row[1]<br>exp = row[2]<br>net = row[3]<br>cnt = row[4]"]
    AccessElements --> CalcTotals["total_inc += inc<br>total_exp += exp<br>if cnt > 0: active_categories += 1<br>if exp > max_expense: top_expense = cat"]
    CalcTotals --> LoopMatrix
    
    LoopMatrix -- ครบทุกแถวแล้ว --> ReturnSummary[/"คืนค่า Dictionary สรุปผลลัพธ์รวม<br>(total_income, total_expense, net_balance, etc.)"/]
    
    ReturnSummary --> RenderTable[/"แสดงผลตาราง Matrix 2 มิติ บนหน้า Dashboard"/]
    RenderTable --> EndMatrix([สิ้นสุด])
```

---

## 4. ตารางเปรียบเทียบ Flowchart กับ Source Code จริง

| องค์ประกอบใน Flowchart | บรรทัดใน Source Code | หน้าที่การทำงาน |
| :--- | :--- | :--- |
| **Authentication Decision (`if`)** | `app.py: 74–79` | ตรวจสอบว่า endpoint ได้รับอนุญาต หรือ session เข้าสู่ระบบแล้วหรือไม่ |
| **Password Match Decision (`if-else`)** | `app.py: 110–115` | ตรวจสอบความถูกต้องของรหัสผ่าน `1234` |
| **File Extension Decision (`if`)** | `app.py: 285–286` | ป้องกันการอัปโหลดไฟล์แปลกปลอม รับเฉพาะ `.jpg, .jpeg, .png` |
| **Image Resize Decision (`if-elif-else`)** | `ocr_service.py: 68–76` | ปรับขนาดภาพตามเกณฑ์ความกว้าง เพื่อให้ OCR ภาษาไทยแม่นยำและรวดเร็ว |
| **Buddhist Era Conversion (`nested-if`)** | `ocr_service.py: 50–57` | แปลงปี พ.ศ. 4 หลัก และ 2 หลัก เป็น ค.ศ. สากล |
| **Month Matching Loop (`nested for`)** | `ocr_service.py: 45–56` | วนลูปเปรียบเทียบชื่อและตัวย่อเดือน 12 เดือน |
| **Amount Validation Loop (`for`)** | `ocr_service.py: 117–124` | วนลูปกรองตัวเลขทศนิยมที่อยู่ในช่วงธุรกรรม 0.50 – 10,000,000 บาท |
| **Duplicate Ref No. Check (`if`)** | `app.py: 301–306` | เรียก `database.find_duplicate_slip()` เพื่อแจ้งเตือนสลิปซ้ำ |
| **2D Nested List Construction Loop (`for`)**| `database.py: 502–513` | วนลูปสร้างแถว `[cat, inc, exp, net, count]` แล้ว `matrix.append(row)` |
| **2D Nested List Index Access Loop (`for`)** | `database.py: 531–545` | วนลูปอ่านข้อมูลผ่าน Index `row[0]`, `row[1]`, `row[2]` ฯลฯ |
