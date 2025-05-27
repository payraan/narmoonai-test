#!/usr/bin/env python3
"""
حل مشکل Bot Conflict در Railway
"""
import requests
import os
import time

def clear_webhook(bot_token):
    """پاک کردن webhook و متوقف کردن سایر instance ها"""
    try:
        print("🔧 Clearing telegram webhook...")
        
        # پاک کردن webhook
        webhook_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
        response = requests.post(webhook_url)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print("✅ Webhook cleared successfully")
            else:
                print(f"⚠️  Webhook clear response: {result}")
        else:
            print(f"❌ Failed to clear webhook: {response.status_code}")
        
        # دریافت pending updates برای پاک کردن
        print("🔄 Getting pending updates...")
        get_updates_url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        
        # دریافت و نادیده گیری pending updates
        for i in range(3):  # حداکثر 3 بار تلاش
            try:
                response = requests.get(get_updates_url, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        updates = result.get("result", [])
                        if updates:
                            # دریافت آخرین update_id
                            last_update_id = max(update.get("update_id", 0) for update in updates)
                            
                            # Acknowledge کردن تمام updates
                            ack_url = f"https://api.telegram.org/bot{bot_token}/getUpdates?offset={last_update_id + 1}"
                            ack_response = requests.get(ack_url, timeout=10)
                            
                            if ack_response.status_code == 200:
                                print(f"✅ Acknowledged {len(updates)} pending updates")
                            else:
                                print(f"⚠️  Ack failed: {ack_response.status_code}")
                        else:
                            print("✅ No pending updates")
                        break
                    else:
                        print(f"❌ Get updates failed: {result}")
                else:
                    print(f"❌ Get updates HTTP error: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"⏳ Timeout on attempt {i+1}, retrying...")
                time.sleep(2)
            except Exception as e:
                print(f"❌ Error on attempt {i+1}: {e}")
                time.sleep(2)
        
        print("✅ Bot conflict resolution completed")
        return True
        
    except Exception as e:
        print(f"❌ Error resolving bot conflict: {e}")
        return False

def main():
    """اجرای اصلی"""
    print("🤖 Telegram Bot Conflict Resolver")
    print("=" * 40)
    
    # دریافت bot token از environment
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not found!")
        return False
    
    print(f"🔑 Bot token: {bot_token[:10]}...")
    
    # حل مشکل conflict
    success = clear_webhook(bot_token)
    
    if success:
        print("\n✅ Conflict resolved!")
        print("🚀 You can now start your bot safely")
        print("⏱️  Wait 5-10 seconds before starting...")
        time.sleep(5)
    else:
        print("\n❌ Failed to resolve conflict")
        print("🔧 Try stopping all Railway services and redeploy")
    
    print("=" * 40)
    return success

if __name__ == "__main__":
    main()
