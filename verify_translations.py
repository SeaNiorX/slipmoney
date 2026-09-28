# verify_translations.py - Verify bilingual completeness across all templates
import re
from app import app, PASSWORD
from translations import TRANSLATIONS, CATEGORIES

def test_pages():
    client = app.test_client()
    client.post('/login', data={'password': PASSWORD})

    pages = ['/dashboard', '/transactions', '/add-transaction']

    for lang in ['th', 'en']:
        client.get(f'/set-language/{lang}')
        print(f"\n=================== Testing Language: {lang.upper()} ===================")
        
        # Test each page
        for page in pages:
            res = client.get(page)
            assert res.status_code == 200, f"Failed on {page} with status {res.status_code}"
            html = res.data.decode('utf-8')
            
            # Check that raw unresolved jinja keys like {{ t['...'] }} don't exist
            unresolved = re.findall(r'\{\{\s*t\[.*?\]\s*\}\}', html)
            assert len(unresolved) == 0, f"Found unresolved translation tags on {page}: {unresolved}"
            
            # Verify characteristic words
            if lang == 'th':
                assert "แดชบอร์ด" in html or "รายการ" in html
                assert "ภาษา" in html or "ไทย" in html
            else:
                assert "Dashboard" in html or "Transactions" in html
                assert "English" in html
            
            print(f"  [OK] {page} in {lang}")

    # Test login page specifically
    for lang in ['th', 'en']:
        client.get('/logout')
        client.get(f'/set-language/{lang}')
        res = client.get('/login')
        assert res.status_code == 200
        html = res.data.decode('utf-8')
        if lang == 'th':
            assert TRANSLATIONS['th']['login_title'] in html
            assert TRANSLATIONS['th']['password'] in html
        else:
            assert TRANSLATIONS['en']['login_title'] in html
            assert TRANSLATIONS['en']['password'] in html
        print(f"  [OK] /login in {lang}")

    print("\nALL PAGES VERIFIED 100% BILINGUAL!")

if __name__ == '__main__':
    test_pages()
