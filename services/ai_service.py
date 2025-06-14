import base64
from openai import OpenAI
from config.settings import OPENAI_API_KEY

# ایجاد کلاینت OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_chart_images(images, strategy_prompt):
    """تحلیل تصاویر چارت با استفاده از OpenAI Vision API"""
    
    try:
        # بررسی اینکه strategy_prompt خالی نباشد
        if not strategy_prompt:
            strategy_prompt = "لطفاً این نمودار را تحلیل کنید و نظر خود را ارائه دهید."
        
        # آماده‌سازی محتوای پیام
        message_content = [
            {
                "type": "text",
                "text": str(strategy_prompt)  # تبدیل به string
            }
        ]
        
        # اضافه کردن تصاویر
        for img_bytes, ext in images:
            # تعیین mime type صحیح
            if ext.lower() in ["jpeg", "jpg"]:
                mime_type = "image/jpeg"
            elif ext.lower() == "png":
                mime_type = "image/png"
            elif ext.lower() == "webp":
                mime_type = "image/webp"
            elif ext.lower() == "gif":
                mime_type = "image/gif"
            else:
                mime_type = "image/jpeg"
            
            # تبدیل به base64
            b64_image = base64.b64encode(img_bytes).decode('utf-8')
            
            # اضافه کردن تصویر
            message_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{b64_image}",
                    "detail": "high"
                }
            })
        
        # ساخت پیام نهایی
        messages = [
            {
                "role": "user",
                "content": message_content
            }
        ]
        
        print(f"🔍 DEBUG: Calling OpenAI with model gpt-4o and {len(images)} images")
        
        # فراخوانی API با مدل صحیح
        response = client.chat.completions.create(
            model="gpt-4o",  # اطمینان از نام صحیح مدل
            messages=messages,
            max_tokens=1300,
            temperature=0.2
        )
        
        result = response.choices[0].message.content
        if not result:
            return "متأسفانه نتوانستم تحلیل مناسبی ارائه دهم. لطفاً دوباره امتحان کنید."
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ OpenAI API Error: {error_msg}")
        
        # بررسی نوع خطا
        if "Invalid content type" in error_msg:
            return "خطا در فرمت تصویر. لطفاً تصویر را در فرمت JPG یا PNG ارسال کنید."
        elif "model" in error_msg.lower():
            return "خطا در مدل هوش مصنوعی. لطفاً بعداً امتحان کنید."
        else:
            return f"خطا در تحلیل: {error_msg}"

# این تابع جدید را به انتهای فایل ai_service.py اضافه کنید

async def get_coach_response(user_prompt: str, image_url: str = None) -> str:
    """
    دریافت پاسخ از ChatGPT با شخصیت "مربی ترید".
    این تابع قابلیت دریافت متن و تصویر را دارد.
    """
    # تعریف شخصیت و دستورالعمل‌های مربی ترید
    system_prompt = """
    You are a professional, risk-averse trading coach and mentor. Your goal is to educate and empower the user, not to provide financial signals.
    - NEVER give direct buy/sell commands.
    - Instead of giving answers, ask guiding questions to make the user think. For example: "What does your trading strategy say here?" or "Have you considered the risk-to-reward ratio?".
    - Always remind the user of risk management and market uncertainty.
    - If you analyze a chart image, explain the patterns, indicators, and potential scenarios (both bullish and bearish).
    - At the end of every message, include this disclaimer:

    ---
    _Disclaimer: I am an AI coach, not a financial advisor. This is not financial advice. All trading decisions and risks are your own._
    """

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # ساختار پیام بر اساس وجود تصویر
    if image_url:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        })
    else:
        messages.append({"role": "user", "content": user_prompt})

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error getting response from OpenAI for Trading Coach: {e}")
        return "❌ متاسفانه در ارتباط با هوش مصنوعی خطایی رخ داد. لطفاً لحظاتی دیگر دوباره تلاش کنید."
