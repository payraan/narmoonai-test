import base64
import logging
from datetime import date
import openai

from config.settings import OPENAI_API_KEY
from database import repository
from resources.prompts.strategies import STRATEGY_PROMPTS

# راه‌اندازی لاگر
logger = logging.getLogger(__name__)

# ایجاد کلاینت Async OpenAI
client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

def encode_image_to_base64(image_path: str) -> str:
    """یک فایل تصویری را به رشته base64 تبدیل می‌کند."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image {image_path}: {e}")
        return None

async def generate_tnt_analaysis(user_id: int, prompt_key: str, photo_path: str = None) -> dict:
    """
    تحلیل تصویر چارت با استفاده از پرامپت‌های TNT.
    این تابع بازنویسی شده تا با ساختار جدید هماهنگ باشد.
    """
    logger.info(f"Generating TNT analysis for user {user_id} with prompt key '{prompt_key}'")
    try:
        # ۱. بررسی اشتراک کاربر
        if not await repository.has_active_tnt_plan(user_id):
            return {"success": False, "error": "NO_ACTIVE_PLAN"}

        # ۲. بارگذاری پرامپت استراتژی
        system_prompt = STRATEGY_PROMPTS.get(prompt_key)
        if not system_prompt:
            logger.error(f"TNT prompt key '{prompt_key}' not found.")
            return {"success": False, "error": "PROMPT_NOT_FOUND"}
        
        # ۳. آماده‌سازی محتوای پیام
        user_content = [{"type": "text", "text": "لطفاً نمودار را بر اساس استراتژی ارائه شده تحلیل کنید."}]
        if photo_path:
            base64_image = encode_image_to_base64(photo_path)
            if base64_image:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                })
        
        # ۴. فراخوانی صحیح OpenAI API
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            max_tokens=1500,
            temperature=0.2
        )
        ai_response = response.choices[0].message.content
        
        # TODO: منطق به‌روزرسانی شمارنده TNT در اینجا پیاده‌سازی شود
        # await repository.update_tnt_usage(...)
        
        return {"success": True, "response": ai_response}

    except Exception as e:
        logger.error(f"Error in generate_tnt_analaysis for user {user_id}: {e}", exc_info=True)
        return {"success": False, "error": "GENERAL_AI_ERROR"}


async def get_trade_coach_response(user_id: int, text_prompt: str, photo_path: str = None) -> dict:
    """
    منطق دریافت پاسخ از مربی ترید را مدیریت می‌کند.
    محدودیت استفاده برای کاربران رایگان را بررسی کرده و OpenAI API را به درستی فراخوانی می‌کند.
    """
    logger.info(f"Getting trade coach response for user_id: {user_id}")
    try:
        # ۱. بررسی اشتراک کاربر
        has_plan = await repository.has_active_tnt_plan(user_id)

        # ۲. بررسی محدودیت برای کاربران رایگان
        if not has_plan:
            today = date.today()
            usage_today = await repository.get_coach_usage(user_id=user_id, usage_date=today)
            current_count = usage_today.message_count if usage_today else 0
            
            if current_count >= 20:
                logger.warning(f"User {user_id} has exceeded the daily limit for Trade Coach.")
                return {"success": False, "error": "LIMIT_EXCEEDED"}

        # ۳. آماده‌سازی پیام برای ارسال به OpenAI
        system_prompt = STRATEGY_PROMPTS.get('trade_coach')
        if not system_prompt:
            logger.error("Trade Coach prompt not found in strategies.")
            return {"success": False, "error": "PROMPT_NOT_FOUND"}

        user_content = [{"type": "text", "text": text_prompt}]
        if photo_path:
            base64_image = encode_image_to_base64(photo_path)
            if base64_image:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                })
        
        # ۴. فراخوانی صحیح OpenAI API با نقش‌های مجزای system و user
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            max_tokens=1200,
            temperature=0.3
        )
        ai_response = response.choices[0].message.content

        # ۵. به‌روزرسانی شمارنده برای کاربران رایگان
        if not has_plan:
            # این تابع در ریپازیتوری شما وجود دارد و فقط user_id و date نیاز دارد
            await repository.increment_coach_usage(user_id=user_id, usage_date=date.today())
        
        logger.info(f"Successfully got trade coach response for user_id: {user_id}")
        return {"success": True, "response": ai_response}

    except Exception as e:
        logger.error(f"Error in get_trade_coach_response for user {user_id}: {e}", exc_info=True)
        return {"success": False, "error": "GENERAL_AI_ERROR"}
