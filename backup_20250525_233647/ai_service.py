import base64
from openai import OpenAI
from config.settings import OPENAI_API_KEY

# ایجاد کلاینت OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_chart_images(images, strategy_prompt):
    """تحلیل تصاویر چارت با استفاده از OpenAI"""
    images_content = []
    
    for img_bytes, ext in images:
        # تعیین mime type
        if ext in ["jpeg", "jpg"]:
            mime = "jpeg"
        elif ext == "png":
            mime = "png"
        elif ext == "webp":
            mime = "webp"
        else:
            mime = "jpeg"
        
        b64img = base64.b64encode(img_bytes).decode('utf-8')
        images_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/{mime};base64,{b64img}",
                "detail": "high"
            }
        })
    
    # پیامی با چند تصویر
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": strategy_prompt}
            ] + images_content
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
        raise Exception(f"خطا در تحلیل تصاویر: {str(e)}")
