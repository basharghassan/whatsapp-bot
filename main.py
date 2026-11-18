import os
from fastapi import FastAPI, Request, HTTPException
import requests

app = FastAPI()

# بيانات الإعداد والتوصيل (توضع في إعدادات البيئة للسيرفر Environment Variables)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# شخصية البوت والتعليمات البرمجية الدقيقة بناءً على طلبك
SYSTEM_PROMPT = """
أنت تمثل فريق عمل المهندس بشار صراميجو، وترد على العملاء عبر واتساب بأسلوب احترافي، مرن، ودود، وطبيعي جداً (وكأنك شخص حقيقي تتحدث معهم، بدون ذكر أنك ذكاء اصطناعي أو مساعد رقمي).

قواعد التعامل:
1. البداية والاستماع: رحب بالعميل بلباقة واسأله مباشرة عن مشروعه أو فكرته أو ما يحتاجه دون سرد قوائم خدمات طويلة.
2. التقييم وإظهار الخبرة: بعد أن يشرح العميل طلبه (سواء في الهوية البصرية، تطوير المواقع، بروفايل الشركات، أو الحلول التقنية)، أظهر له أنك فهمت فكرته بدقة، وأكد له بثقة أن لدينا الخبرة التقنية والتصميمية والفنية الكاملة لتنفيذها بأعلى جودة.
3. المرونة والنقاش: ناقش معه التفاصيل بمرونة واسأله أسئلة ذكية لتوضيح الصورة (مثل طبيعة النشاط أو الموعد).
4. الاعتماد والتنبيه: بمجرد أن يوافق العميل نهائياً أو يطلب البدء الفعلي، رحب بقراره وأنهِ ردك حصراً بكلمة [DEAL_AGREED] ليتم إشعار المهندس بشار صراميجو فوراً.
"""

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    try:
        # التحقق من وصول رسالة صحيحة من واتساب
        entry = data.get("entry", [])[0]
        change = entry.get("changes", [])[0]
        value = change.get("value", {})
        
        if "messages" in value:
            message_data = value["messages"][0]
            sender_phone = message_data["from"]
            sender_name = value.get("contacts", [{}])[0].get("profile", {}).get("name", "عميل")
            message_body = message_data.get("text", {}).get("body", "")

            # 1. استدعاء نموذج الذكاء الاصطناعي مع القواعد
            ai_response = ask_ai_model(sender_phone, message_body)

            # 2. التحقق من موافقة العميل النهائية (الاتفاق)
            if "[DEAL_AGREED]" in ai_response:
                clean_response = ai_response.replace("[DEAL_AGREED]", "").strip()
                # إرسال إشعار فوري لك على تليجرام
                send_telegram_alert(sender_name, sender_phone, message_body)
            else:
                clean_response = ai_response

            # 3. إرسال الرد العائد إلى العميل عبر واتساب
            send_whatsapp_message(sender_phone, clean_response)

    except Exception as e:
        print(f"Error processing webhook: {e}")
    
    return {"status": "ok"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    # مخصص للتحقق من Meta API عند ربط الـ Webhook
    verify_token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if verify_token == "bashar_secure_token_2026":
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification token mismatch")

def ask_ai_model(sender_id, text):
    # هنا يتم تمرير النص لنموذج الذكاء الاصطناعي مع تفعيل الـ System Prompt
    return "أهلاً بك يا غالي! يسعدني جداً سماع فكرتك، شاركني تفاصيل أكثر عن مشروعك لنشوف كيف نقدر ننفذه بأفضل شكل تقني وتصميمي يناسبك."

def send_whatsapp_message(recipient_phone, text):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, headers=headers, json=payload)

def send_telegram_alert(name, phone, details):
    msg = f"🚨 تنبيه اتفاق وعميل جديد!\n👤 اسم العميل: {name}\n📱 رقم الهاتف: {phone}\n💬 آخر تفاصيل: {details}\n\nيُرجى التدخل الآن ومباشرة العمل!"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg
    }
    requests.post(url, json=payload)
