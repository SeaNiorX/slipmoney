# ocr_service.py - Enhanced OCR extraction engine for SlipMoney
import os
import re
import datetime
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract

# Configure Tesseract path
TESSERACT_EXE = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_EXE):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
TESSDATA_DIR = os.path.join(PROJECT_DIR, "tessdata")
if os.path.exists(TESSDATA_DIR):
    os.environ["TESSDATA_PREFIX"] = TESSDATA_DIR

# Comprehensive Month mapping supporting Thai (abbreviations, full names, OCR artifacts) and English
MONTH_GROUPS = {
    1: ['มกราคม', 'มกรา', 'ม.ค.', 'ม.ค', 'มค', 'jan', 'january'],
    2: ['กุมภาพันธ์', 'กุมภา', 'ก.พ.', 'ก.พ', 'กพ', 'feb', 'february'],
    3: ['มีนาคม', 'มีนา', 'มี.ค.', 'มี.ค', 'มีค', 'mar', 'march'],
    4: ['เมษายน', 'เมษา', 'เม.ย.', 'เม.ย', 'เมย', 'เม.บ', 'เมบ', 'apr', 'april'],
    5: ['พฤษภาคม', 'พฤษภา', 'พ.ค.', 'พ.ค', 'พค', 'may'],
    6: ['มิถุนายน', 'มิถุนา', 'มิ.ย.', 'มิ.ย', 'มิย', 'มิ.บ', 'มิบ', 'jun', 'june'],
    7: ['กรกฎาคม', 'กรกฎา', 'ก.ค.', 'ก.ค', 'กค', 'jul', 'july'],
    8: ['สิงหาคม', 'สิงหา', 'ส.ค.', 'ส.ค', 'สค', 'aug', 'august'],
    9: ['กันยายน', 'กันยา', 'ก.ย.', 'ก.ย', 'กย', 'กุย', 'ทุย', 'ท.ย', 'ทย', 'ก.บ', 'กบ', 'n.d', 'n.al', 'sep', 'sept', 'september'],
    10: ['ตุลาคม', 'ตุลา', 'ต.ค.', 'ต.ค', 'ตค', 'oct', 'october'],
    11: ['พฤศจิกายน', 'พฤศจิกา', 'พ.ย.', 'พ.ย', 'พย', 'พ.บ', 'พบ', 'nov', 'november'],
    12: ['ธันวาคม', 'ธันวา', 'ธ.ค.', 'ธ.ค', 'ธค', 'dec', 'december']
}

def match_month(token):
    """Fuzzy match a text token to a month number 1-12"""
    if not token:
        return None
    clean = token.strip('. -/').lower()
    for m_num, variants in MONTH_GROUPS.items():
        for v in variants:
            v_clean = v.strip('. ').lower()
            if clean == v_clean or clean.startswith(v_clean) or v_clean in clean:
                return m_num
    return None

def clean_year(raw_year):
    """Normalize 2-digit, 4-digit Buddhist (BE) and Christian (CE) years"""
    year = int(raw_year)
    if year > 2400: # Thai Buddhist Era e.g. 2567, 2569
        year -= 543
    elif year < 100:
        if year >= 50: # 2-digit Buddhist Era e.g. 67 -> 2024, 69 -> 2026
            year = (2500 + year) - 543
        else: # 2-digit CE e.g. 24 -> 2024, 26 -> 2026
            year = 2000 + year
    return year

def preprocess_image(image_path):
    """
    Load image, transpose EXIF orientation, resize to ideal OCR scale,
    and generate enhanced variants (grayscale + contrast).
    """
    images = []
    try:
        raw_img = Image.open(image_path)
        # Fix orientation from mobile phone cameras (EXIF)
        orig = ImageOps.exif_transpose(raw_img).convert('RGB')
        
        # Scale image to optimal OCR dimensions (width around 1200-1500px)
        w, h = orig.size
        if w > 1800:
            target_w = 1500
            target_h = int(h * (target_w / w))
            scaled = orig.resize((target_w, target_h), Image.Resampling.LANCZOS)
        elif w < 800:
            target_w = 1200
            target_h = int(h * (target_w / w))
            scaled = orig.resize((target_w, target_h), Image.Resampling.BICUBIC)
        else:
            scaled = orig

        images.append(scaled)

        # Variant 1: Grayscale + high contrast
        gray = scaled.convert('L')
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(1.8)
        images.append(enhanced)

        # Variant 2: Slightly sharpened
        sharpened = enhanced.filter(ImageFilter.SHARPEN)
        images.append(sharpened)

    except Exception as e:
        print(f"Image preprocessing error: {e}")
    return images

def parse_amount(text):
    """
    Extract transaction amount from OCR text.
    """
    if not text:
        return None

    normalized = text.replace('\xa0', ' ')

    # 1. Keywords followed directly by amount
    keyword_patterns = [
        r'(?:จำนวนเงิน|จำนวน|ยอดเงิน|ยอดโอน|amount|total|paid|ชำระ)[\s:=]*[^\d\n\r]{0,5}([\d,]+(?:\.\d{1,2})?)',
        r'([฿\$\s]*[\d,]+(?:\.\d{2}))\s*(?:บาท|baht|thb)',
        r'[฿]\s*([\d,]+(?:\.\d{2})?)',
    ]

    for pat in keyword_patterns:
        match = re.search(pat, normalized, re.IGNORECASE)
        if match:
            raw_val = match.group(1).replace('฿', '').replace('$', '').replace(',', '').strip()
            raw_val = re.sub(r'^[^\d]+', '', raw_val)
            try:
                val = float(raw_val)
                if val > 0:
                    return f"{val:.2f}"
            except ValueError:
                pass

    # 2. General decimal numbers with 2 decimal places
    decimal_matches = re.findall(r'(?<![:\d])(\d{1,3}(?:,\d{3})*\.\d{2})(?![\d])', normalized)
    valid_amounts = []
    for m in decimal_matches:
        raw_val = m.replace(',', '').strip()
        try:
            val = float(raw_val)
            if 0.50 <= val <= 10000000:
                valid_amounts.append(val)
        except ValueError:
            pass

    if valid_amounts:
        return f"{valid_amounts[0]:.2f}"

    # 3. Whole numbers followed by 'บาท'
    whole_match = re.search(r'\b(\d{1,3}(?:,\d{3})*|\d+)\s*(?:บาท|baht|thb)\b', normalized, re.IGNORECASE)
    if whole_match:
        raw_val = whole_match.group(1).replace(',', '').strip()
        try:
            val = float(raw_val)
            if val > 0:
                return f"{val:.2f}"
        except ValueError:
            pass

    return None

def parse_date(text):
    """
    Extract date and convert to standard YYYY-MM-DD.
    Handles:
    - 28 ก.ย. 67, 28 กย 67, 28 ก.ย. 2567, 25 ทุย. 2569, 25 กุย. 2569
    - 28 Sep 2024, 28 Sep 24, 28-Sep-2024, September 28, 2026
    - 28/09/2026, 28/09/2567, 28-09-2024, 28.09.67
    - 2026-09-28, 2567-09-28
    """
    if not text:
        return None

    normalized = text.replace('\xa0', ' ')

    # 1. Day + Month (Name/Abbr/OCR variant) + Year
    # e.g., 25 ทุย. 2569, 28 Sep 2024, 15 กรกฎาคม 2567
    pat_dmy = r'(\b\d{1,2})\s*[-\/.\s]?\s*([A-Za-zก-๙\.]+)\s*[-\/.\s]?\s*(\d{2,4})'
    for match in re.finditer(pat_dmy, normalized):
        day = int(match.group(1))
        month = match_month(match.group(2))
        if month and 1 <= month <= 12 and 1 <= day <= 31:
            year = clean_year(match.group(3))
            try:
                return datetime.date(year, month, day).strftime('%Y-%m-%d')
            except ValueError:
                pass

    # 2. Month + Day + Year (e.g. Sep 25, 2026 or September 25 2026)
    pat_mdy = r'\b([A-Za-zก-๙\.]+)\s+(\d{1,2})(?:st|nd|rd|th)?[\s,]+(\d{2,4})\b'
    for match in re.finditer(pat_mdy, normalized):
        month = match_month(match.group(1))
        day = int(match.group(2))
        if month and 1 <= month <= 12 and 1 <= day <= 31:
            year = clean_year(match.group(3))
            try:
                return datetime.date(year, month, day).strftime('%Y-%m-%d')
            except ValueError:
                pass

    # 3. DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
    dmy = re.findall(r'(\b\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2,4})\b', normalized)
    for d_str, m_str, y_str in dmy:
        day = int(d_str)
        month = int(m_str)
        year = clean_year(y_str)
        if 1 <= month <= 12 and 1 <= day <= 31:
            try:
                return datetime.date(year, month, day).strftime('%Y-%m-%d')
            except ValueError:
                pass

    # 4. YYYY/MM/DD or YYYY-MM-DD
    ymd = re.findall(r'\b(20\d{2}|25\d{2})[\/\.-](\d{1,2})[\/\.-](\d{1,2})\b', normalized)
    for y_str, m_str, d_str in ymd:
        year = clean_year(y_str)
        month = int(m_str)
        day = int(d_str)
        if 1 <= month <= 12 and 1 <= day <= 31:
            try:
                return datetime.date(year, month, day).strftime('%Y-%m-%d')
            except ValueError:
                pass

    return None

def parse_time(text):
    """
    Extract time and convert to standard HH:MM (24-hour).
    Handles:
    - 14:32, 14:32:05
    - 14.32 น., 14.32น, 14 : 32
    - เวลา 14:32, Time 14:32
    - Time immediately after date e.g. '28/09/2026 1432'
    """
    if not text:
        return None

    normalized = text.replace('\xa0', ' ')

    # 1. Explicit keywords: e.g. เวลา 14:32 or เวลา 14.32 or Time: 14:32
    kw_time = re.findall(r'(?:เวลา|time|at)\s*[:.]?\s*([01]?\d|2[0-3])\s*[:.;]\s*([0-5]\d)\b', normalized, re.IGNORECASE)
    for h_str, m_str in kw_time:
        hour = int(h_str)
        minute = int(m_str)
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"

    # 2. Thai dot time with น. or hrs/am/pm: e.g. 14.32 น. or 14.32น or 14.32 hrs
    dot_matches = re.findall(r'\b([01]?\d|2[0-3])\s*[.]\s*([0-5]\d)\s*(?:น\.?|hrs|am|pm)', normalized, re.IGNORECASE)
    for h_str, m_str in dot_matches:
        hour = int(h_str)
        minute = int(m_str)
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"

    # 3. Standard colon time: e.g. 14:32, 09:15, with boundary
    colon_matches = re.findall(r'\b([01]?\d|2[0-3])\s*[:]\s*([0-5]\d)\b', normalized)
    for h_str, m_str in colon_matches:
        hour = int(h_str)
        minute = int(m_str)
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"

    return None

def parse_ref_no(text):
    """
    Extract bank transaction reference number / code from slip text.
    Handles:
    - รหัสอ้างอิง Ab52b1fa1d6724c85
    - เลขที่อ้างอิง, หมายเลขอ้างอิง, เลขที่รายการ, Ref No., Reference No., Txn ID
    """
    if not text:
        return None

    normalized = text.replace('\xa0', ' ')

    patterns = [
        # Explicit reference keywords followed by alphanumeric string
        r'(?:รหัสอ้างอิง|เลขที่อ้างอิง|หมายเลขอ้างอิง|เลขที่รายการ|เลขที่สลิป|รหัสธุรกรรม|ref(?:\s*no\.?|\.?)|trans(?:\s*ref\.?|\.?)|reference(?:\s*no\.?|\.?)|txn(?:\s*id\.?|\.?))[\s:=]*([a-zA-Z0-9]{8,35})',
        # Word boundary matching ref / txn codes
        r'\b(?:ref|txn)[\s:.-]*([a-zA-Z0-9]{10,35})\b',
    ]

    for pat in patterns:
        matches = re.findall(pat, normalized, re.IGNORECASE)
        for ref in matches:
            ref_clean = ref.strip()
            # Ensure it is not just a pure timestamp/date
            if len(ref_clean) >= 8 and (not ref_clean.isdigit() or len(ref_clean) >= 12):
                return ref_clean

    return None

def process_slip(image_path):
    """
    Runs OCR on the given image and extracts amount, date, time, and ref_no.
    Returns:
    {
        "amount": "90.00" or None,
        "date": "2026-09-25" or None,
        "time": "11:46" or None,
        "ref_no": "Ab52b1fa1d6724c85" or None,
        "has_amount": bool,
        "has_date": bool,
        "has_time": bool,
        "has_ref_no": bool,
        "raw_text": "...",
        "success": bool
    }
    """
    if not os.path.exists(image_path):
        return {
            "amount": None, "date": None, "time": None, "ref_no": None,
            "has_amount": False, "has_date": False, "has_time": False, "has_ref_no": False,
            "raw_text": "", "success": False
        }

    images = preprocess_image(image_path)
    combined_text = ""

    langs = ['tha+eng', 'eng']
    
    for img in images:
        for lang in langs:
            try:
                txt = pytesseract.image_to_string(img, lang=lang)
                if txt:
                    combined_text += "\n" + txt
            except Exception:
                try:
                    txt = pytesseract.image_to_string(img, lang='eng')
                    combined_text += "\n" + txt
                except Exception:
                    pass

    amount = parse_amount(combined_text)
    date = parse_date(combined_text)
    time = parse_time(combined_text)
    ref_no = parse_ref_no(combined_text)

    return {
        "amount": amount,
        "date": date,
        "time": time,
        "ref_no": ref_no,
        "has_amount": amount is not None,
        "has_date": date is not None,
        "has_time": time is not None,
        "has_ref_no": ref_no is not None,
        "raw_text": combined_text.strip(),
        "success": bool(combined_text.strip())
    }
