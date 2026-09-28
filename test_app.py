# test_app.py - Comprehensive verification test suite for SlipMoney
import os
import io
import unittest
from app import app, PASSWORD
from translations import TRANSLATIONS, CATEGORIES
import database
from PIL import Image, ImageDraw

class SlipMoneyTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_translations_integrity(self):
        """Ensure all keys exist in both Thai and English dictionaries"""
        th_keys = set(TRANSLATIONS['th'].keys())
        en_keys = set(TRANSLATIONS['en'].keys())
        
        diff_th = en_keys - th_keys
        diff_en = th_keys - en_keys
        
        self.assertEqual(len(diff_th), 0, f"Keys in en but missing in th: {diff_th}")
        self.assertEqual(len(diff_en), 0, f"Keys in th but missing in en: {diff_en}")

        # Check category keys
        for cat in CATEGORIES:
            self.assertIn(cat['key'], TRANSLATIONS['th'])
            self.assertIn(cat['key'], TRANSLATIONS['en'])

    def test_02_authentication_and_protection(self):
        """Test authentication flow and route protection"""
        # 1. Access dashboard without login -> should redirect to login
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

        # 2. Login with wrong password -> fails
        res = self.client.post('/login', data={'password': 'wrongpassword'}, follow_redirects=True)
        self.assertIn(TRANSLATIONS['th']['invalid_password'].encode('utf-8'), res.data)

        # 3. Login with correct password '1234' -> succeeds and redirects to dashboard
        res = self.client.post('/login', data={'password': PASSWORD}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(TRANSLATIONS['th']['dashboard'].encode('utf-8'), res.data)

    def test_03_bilingual_switching(self):
        """Test switching language between Thai and English"""
        with self.client:
            # Login first
            self.client.post('/login', data={'password': PASSWORD})
            
            # Switch to English
            res = self.client.get('/set-language/en', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Total Income", res.data)
            self.assertIn(b"Total Expenses", res.data)
            self.assertIn(b"Balance", res.data)
            self.assertIn(b"Hello", res.data)

            # Switch back to Thai
            res = self.client.get('/set-language/th', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(TRANSLATIONS['th']['total_income'].encode('utf-8'), res.data)
            self.assertIn(TRANSLATIONS['th']['greeting'].encode('utf-8'), res.data)

    def test_04_add_and_list_transactions(self):
        """Test adding a transaction and viewing it in list and dashboard"""
        with self.client:
            self.client.post('/login', data={'password': PASSWORD})

            # Add an expense
            res = self.client.post('/add-transaction', data={
                'type': 'expense',
                'amount': '320.50',
                'date': '2026-09-28',
                'time': '12:30',
                'category': 'food',
                'description': 'Test Lunch Item'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Test Lunch Item', res.data)
            self.assertIn(b'320.50', res.data)

    def test_05_ocr_api(self):
        """Test OCR API endpoint with an in-memory test image"""
        with self.client:
            self.client.post('/login', data={'password': PASSWORD})

            # Generate in-memory slip
            img = Image.new('RGB', (400, 200), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            d.text((20, 20), "Amount: 450.00 Baht", fill=(0, 0, 0))
            d.text((20, 60), "28/09/2026 15:45", fill=(0, 0, 0))
            
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)

            res = self.client.post('/api/ocr-slip', data={
                'slip': (img_bytes, 'test_slip.jpg')
            }, content_type='multipart/form-data')

            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data['success'])
            self.assertEqual(data['amount'], '450.00')
            self.assertEqual(data['date'], '2026-09-28')
            self.assertEqual(data['time'], '15:45')
            self.assertTrue(data['filename'].startswith('slip_'))

    def test_06_delete_transaction(self):
        """Test deleting a transaction"""
        with self.client:
            self.client.post('/login', data={'password': PASSWORD})

            tx_id = database.add_transaction('expense', 99.00, '2026-09-28', '11:00', 'other', 'Item to delete')
            res = self.client.post(f'/api/delete-transaction/{tx_id}', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIsNone(database.get_transaction_by_id(tx_id))

    def test_07_logout(self):
        """Test logout functionality"""
        with self.client:
            self.client.post('/login', data={'password': PASSWORD})
            res = self.client.get('/logout', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            
            # Now verify dashboard is protected again
            res2 = self.client.get('/dashboard')
            self.assertEqual(res2.status_code, 302)

if __name__ == '__main__':
    unittest.main()
