import redis
import json
import pickle
import os
from typing import Any, Optional
from datetime import timedelta

class RedisCacheService:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL") or os.getenv("Redis_URL")
        self.redis_client = None
        self.default_ttl = 300  # 5 دقیقه
        self._connect()
    
    def _connect(self):
        """اتصال به Redis"""
        try:
            if self.redis_url:
                print(f"🔗 Connecting to Redis: {self.redis_url[:20]}...")
                self.redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=False,  # برای پشتیبانی از pickle
                    socket_connect_timeout=10,
                    socket_timeout=10,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # تست اتصال
                self.redis_client.ping()
                print("✅ Redis connection successful!")
            else:
                print("⚠️ No Redis URL found, falling back to memory cache")
                self.redis_client = None
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            print("📝 Falling back to memory cache")
            self.redis_client = None
    
    def _serialize(self, value: Any) -> bytes:
        """سریالایز کردن داده"""
        try:
            # ابتدا JSON را امتحان کن
            return json.dumps(value, ensure_ascii=False).encode('utf-8')
        except (TypeError, ValueError):
            # اگر JSON کار نکرد، از pickle استفاده کن
            return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """دی‌سریالایز کردن داده"""
        try:
            # ابتدا JSON را امتحان کن
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # اگر JSON کار نکرد، از pickle استفاده کن
            return pickle.loads(data)
    
    def get(self, key: str) -> Optional[Any]:
        """دریافت از کش"""
        if not self.redis_client:
            return self._memory_get(key)
        
        try:
            data = self.redis_client.get(f"narmoon:{key}")
            if data:
                return self._deserialize(data)
            return None
        except Exception as e:
            print(f"Redis get error for key {key}: {e}")
            return self._memory_get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """ذخیره در کش"""
        if not self.redis_client:
            return self._memory_set(key, value, ttl)
        
        try:
            data = self._serialize(value)
            ttl = ttl or self.default_ttl
            result = self.redis_client.setex(f"narmoon:{key}", ttl, data)
            return bool(result)
        except Exception as e:
            print(f"Redis set error for key {key}: {e}")
            return self._memory_set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """حذف از کش"""
        if not self.redis_client:
            return self._memory_delete(key)
        
        try:
            result = self.redis_client.delete(f"narmoon:{key}")
            return bool(result)
        except Exception as e:
            print(f"Redis delete error for key {key}: {e}")
            return self._memory_delete(key)
    
    def exists(self, key: str) -> bool:
        """بررسی وجود کلید"""
        if not self.redis_client:
            return self._memory_exists(key)
        
        try:
            return bool(self.redis_client.exists(f"narmoon:{key}"))
        except Exception as e:
            print(f"Redis exists error for key {key}: {e}")
            return self._memory_exists(key)
    
    def clear_pattern(self, pattern: str) -> int:
        """حذف کلیدهای با الگو"""
        if not self.redis_client:
            return self._memory_clear_pattern(pattern)
        
        try:
            keys = self.redis_client.keys(f"narmoon:{pattern}")
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Redis clear pattern error: {e}")
            return self._memory_clear_pattern(pattern)
    
    def get_ttl(self, key: str) -> int:
        """دریافت زمان باقی‌مانده تا انقضا"""
        if not self.redis_client:
            return -1  # برای memory cache TTL پیاده‌سازی نشده
        
        try:
            return self.redis_client.ttl(f"narmoon:{key}")
        except Exception as e:
            print(f"Redis TTL error for key {key}: {e}")
            return -1
    
    def extend_ttl(self, key: str, additional_seconds: int) -> bool:
        """افزایش زمان انقضا"""
        if not self.redis_client:
            return False
        
        try:
            current_ttl = self.redis_client.ttl(f"narmoon:{key}")
            if current_ttl > 0:
                new_ttl = current_ttl + additional_seconds
                return bool(self.redis_client.expire(f"narmoon:{key}", new_ttl))
        except Exception as e:
            print(f"Redis extend TTL error for key {key}: {e}")
        return False
    
    # === Fallback Memory Cache ===
    def __init_memory_cache(self):
        """ایجاد کش حافظه اگر وجود نداشته باشد"""
        if not hasattr(self, '_memory_cache'):
            self._memory_cache = {}
            self._memory_timestamps = {}
    
    def _memory_get(self, key: str) -> Optional[Any]:
        """دریافت از کش حافظه"""
        import time
        self.__init_memory_cache()
        
        if key in self._memory_cache:
            # بررسی انقضا
            if time.time() - self._memory_timestamps[key] < self.default_ttl:
                return self._memory_cache[key]
            else:
                # حذف داده منقضی شده
                del self._memory_cache[key]
                del self._memory_timestamps[key]
        return None
    
    def _memory_set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """ذخیره در کش حافظه"""
        import time
        self.__init_memory_cache()
        
        self._memory_cache[key] = value
        self._memory_timestamps[key] = time.time()
        return True
    
    def _memory_delete(self, key: str) -> bool:
        """حذف از کش حافظه"""
        self.__init_memory_cache()
        
        if key in self._memory_cache:
            del self._memory_cache[key]
            del self._memory_timestamps[key]
            return True
        return False
    
    def _memory_exists(self, key: str) -> bool:
        """بررسی وجود در کش حافظه"""
        self.__init_memory_cache()
        return key in self._memory_cache
    
    def _memory_clear_pattern(self, pattern: str) -> int:
        """حذف کلیدهای با الگو از کش حافظه"""
        self.__init_memory_cache()
        
        import fnmatch
        keys_to_delete = [key for key in self._memory_cache.keys() 
                         if fnmatch.fnmatch(key, pattern)]
        
        for key in keys_to_delete:
            del self._memory_cache[key]
            if key in self._memory_timestamps:
                del self._memory_timestamps[key]
        
        return len(keys_to_delete)
    
    def health_check(self) -> dict:
        """بررسی سلامت Redis"""
        health_info = {
            "redis_connected": False,
            "redis_url_configured": bool(self.redis_url),
            "fallback_memory": False,
            "test_write": False,
            "test_read": False
        }
        
        if self.redis_client:
            try:
                # تست ping
                self.redis_client.ping()
                health_info["redis_connected"] = True
                
                # تست write/read
                test_key = "health_check_test"
                test_value = {"timestamp": "test", "data": [1, 2, 3]}
                
                if self.set(test_key, test_value, 60):
                    health_info["test_write"] = True
                    
                    retrieved = self.get(test_key)
                    if retrieved == test_value:
                        health_info["test_read"] = True
                    
                    # پاک کردن تست
                    self.delete(test_key)
                
            except Exception as e:
                print(f"Redis health check failed: {e}")
                health_info["fallback_memory"] = True
        else:
            health_info["fallback_memory"] = True
        
        return health_info

# نمونه global
redis_cache = RedisCacheService()
