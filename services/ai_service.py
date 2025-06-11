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
