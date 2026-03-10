import requests
import re

def redeem_truemoney_voucher(voucher_link: str, phone_number: str):
    # แกะรหัสแฮชจากลิงก์
    match = re.search(r'v=([a-zA-Z0-9]+)', voucher_link)
    if not match:
        return {"status": "error", "message": "รูปแบบลิงก์ไม่ถูกต้อง"}
    
    voucher_hash = match.group(1)
    api_url = f"https://gift.truemoney.com/campaign/vouchers/{voucher_hash}/redeem"
    
    payload = {
        "mobile": phone_number,
        "voucher_hash": voucher_hash
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        result = response.json()
        
        if result.get("status") == "SUCCESS":
            amount = result["data"]["voucher"]["redeemed_amount_baht"]
            return {"status": "success", "amount": amount, "message": "รับเงินสำเร็จ"}
        else:
            return {"status": "error", "message": result.get("status", "รับเงินไม่สำเร็จ (ซองอาจเต็ม/หมดอายุ)")}
            
    except Exception as e:
        return {"status": "error", "message": f"เกิดข้อผิดพลาด: {str(e)}"}