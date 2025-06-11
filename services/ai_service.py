import base64
from openai import OpenAI
from config.settings import OPENAI_API_KEY

# ایجاد کلاینت OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_chart_images(images, strategy_prompt):
    """تحلیل تصاویر چارت با استفاده از OpenAI Vision API"""
    
    # آماده‌سازی محتوای پیام
    message_content = [
        {
            "type": "text",
            "text": strategy_prompt
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
            mime_type = "image/jpeg"  # پیش‌فرض
        
        # تبدیل به base64
        b64_image = base64.b64encode(img_bytes).decode('utf-8')
        
        # اضافه کردن تصویر به پیام
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
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1300,
            temperature=0.2
        )
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")
