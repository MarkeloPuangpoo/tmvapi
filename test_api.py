import requests

# 1. ตั้งค่า URL ของ API เรา
api_url = "http://127.0.0.1:8000/api/redeem"

# 2. จำลองว่าบอท Discord ส่ง API Key มาใน Header
headers = {
    "x-api-key": "sk_test_12345"
}

# 3. จำลองลิงก์ซองที่ลูกค้าพิมพ์ใน Discord (ลองสร้างซอง 1 บาท ส่งให้ตัวเองเพื่อเอาลิงก์มาเทสต์ได้ครับ)
payload = {
    "link": "https://gift.truemoney.com/campaign/?v=ใส่รหัสแฮชของซองตรงนี้"
}

# 4. ยิง Request!
response = requests.post(api_url, headers=headers, json=payload)

# 5. ดูผลลัพธ์
print(response.json())