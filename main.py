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
    # 1. เช็คว่าใส่ API Key มาไหม
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key in headers")
    
    # 2. วิ่งไปค้นหา API Key ในฐานข้อมูล Supabase ตาราง 'api_keys'
    try:
        response = supabase.table("api_keys").select("*").eq("api_key", x_api_key).execute()
        records = response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

    # 3. ตรวจสอบว่าเจอ Key นี้ไหม
    if not records or len(records) == 0:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    user_data = records[0] # ข้อมูลลูกค้าเจ้าของ Key นี้
    
    # 4. ดึงเบอร์โทรที่ลูกค้าผูกไว้ (Hardware Binding)
    locked_phone = user_data.get("locked_phone")
    if not locked_phone:
        raise HTTPException(status_code=400, detail="No phone number bound to this API Key. Please bind it on the dashboard.")

    # 5. (Optional) เช็คโควต้าว่าเหลือไหม
    # if user_data.get("plan_type") == "starter" and user_data.get("quota_left", 0) <= 0:
    #     raise HTTPException(status_code=402, detail="Quota exceeded. Please top up.")

    # 6. ส่งลิงก์กับเบอร์โทรที่ดึงจาก DB ไปรับเงิน
    result = redeem_truemoney_voucher(req.link, locked_phone)

    # 7. (Optional) ถ้าตั้งใจจะหักโควต้าเมื่อรับซองสำเร็จ ให้เขียนอัปเดต DB ตรงนี้
    # if result["status"] == "success" and user_data.get("plan_type") == "starter":
    #     new_quota = user_data["quota_left"] - 1
    #     supabase.table("api_keys").update({"quota_left": new_quota}).eq("api_key", x_api_key).execute()

    return result