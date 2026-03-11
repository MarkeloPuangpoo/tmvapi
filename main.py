from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from truemoney import redeem_truemoney_voucher
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# โหลดค่าลับจากไฟล์ .env
load_dotenv()

# ตั้งค่าการเชื่อมต่อ Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ตรวจสอบว่าใส่ URL กับ Key ครบไหม
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase credentials are not set in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="TrueMoney Wallet API by SaaS")

# ลูกค้าส่งมาแค่ลิงก์ซอง ไม่ต้องส่งเบอร์โทรแล้ว!
class RedeemRequest(BaseModel):
    link: str

@app.get("/")
def read_root():
    return {"message": "API is Online and ready!"}

@app.post("/api/redeem")
def redeem_api(req: RedeemRequest, x_api_key: str = Header(None)):
    # 1. เช็ค API Key
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key in headers")
    
    # 2. ค้นหา API Key ในฐานข้อมูล
    try:
        response = supabase.table("api_keys").select("*").eq("api_key", x_api_key).execute()
        records = response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

    if not records or len(records) == 0:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    user_data = records[0] 
    api_key_id = user_data.get("id") # ดึง ID ของคีย์นี้มาเพื่อใช้เป็น Foreign Key
    locked_phone = user_data.get("locked_phone")
    
    if not locked_phone:
        raise HTTPException(status_code=400, detail="No phone number bound to this API Key.")

    # 3. ส่งลิงก์กับเบอร์โทรไปรับเงิน
    result = redeem_truemoney_voucher(req.link, locked_phone)

    # 4. 📝 [ส่วนที่เพิ่มใหม่] บันทึกประวัติลงตาราง api_logs
    log_status = result.get("status", "error")
    log_amount = result.get("amount", 0.0) if log_status == "success" else 0.0

    try:
        supabase.table("api_logs").insert({
            "api_key_id": api_key_id,
            "voucher_link": req.link,
            "status": log_status,
            "amount": log_amount
        }).execute()
    except Exception as e:
        # พิมพ์ Error ไว้ดูใน Log ของ Render แต่ไม่ต้องทำให้ API พัง เพราะลูกค้ารับเงินไปแล้ว
        print(f"Failed to save log: {str(e)}")

    # 5. หักโควต้า (ถ้าเป็นแพ็กเกจ starter และรับซองสำเร็จ)
    if log_status == "success" and user_data.get("plan_type") == "starter":
        new_quota = user_data.get("quota_left", 0) - 1
        try:
            supabase.table("api_keys").update({"quota_left": new_quota}).eq("api_key", x_api_key).execute()
        except Exception as e:
            print(f"Failed to update quota: {str(e)}")

    return result