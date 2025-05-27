import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from config.settings import API_KEYS, BASE_URLS
from utils.helpers import cache, cache_result, format_large_number

class CryptoAPIService:
    def __init__(self):
        self.api_keys = API_KEYS
        self.base_urls = BASE_URLS
        # استفاده از API خارجی که آماده کردی
        self.external_api_base = "https://web-production-8ccb1.up.railway.app"
        
    def _make_request(self, url: str, headers: Dict = None, params: Dict = None) -> Dict:
        """درخواست HTTP با مدیریت خطا"""
        try:
            # اضافه کردن timeout
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            return {"error": "Timeout", "message": "درخواست طولانی شد"}
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return {"error": "RequestError", "message": str(e)}
        except json.JSONDecodeError:
            return {"error": "JSONError", "message": "پاسخ نامعتبر"}
    
    @cache_result("market_overview", ttl=300)  # 5 دقیقه کش
    async def get_market_overview(self) -> Dict[str, Any]:
        """دریافت نمای کلی بازار با Redis Cache"""
        try:
            # استفاده از CoinGecko Global API
            url = f"{self.external_api_base}/api/coingecko/global"
            response = self._make_request(url)
            
            if "error" not in response and "data" in response:
                data = response["data"]
                
                result = {
                    "btc_dominance": data.get("market_cap_percentage", {}).get("btc", 0),
                    "total_market_cap": data.get("total_market_cap", {}).get("usd", 0),
                    "total_volume": data.get("total_volume", {}).get("usd", 0),
                    "market_cap_change_24h": data.get("market_cap_change_percentage_24h_usd", 0),
                    "active_cryptocurrencies": data.get("active_cryptocurrencies", 0),
                    "timestamp": datetime.now().isoformat()
                }
                
                # دریافت قیمت کوین‌های اصلی
                coins_data = await self._get_main_coins_prices()
                result["main_coins"] = coins_data
                
                return result
            
            return {
                "error": True,
                "message": "خطا در دریافت اطلاعات بازار"
            }
            
        except Exception as e:
            print(f"Error in get_market_overview: {e}")
            return {
                "error": True,
                "message": "خطا در دریافت اطلاعات بازار"
            }
    
    @cache_result("main_coins_prices", ttl=120)  # 2 دقیقه کش
    async def _get_main_coins_prices(self) -> Dict[str, Any]:
        """دریافت قیمت کوین‌های اصلی با کش"""
        try:
            url = f"{self.external_api_base}/api/cryptocompare/price"
            coins = {}
            
            # دریافت قیمت هر کوین جداگانه
            for symbol in ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE"]:
                params = {"fsym": symbol, "tsyms": "USD"}
                response = self._make_request(url, params=params)
                
                if "error" not in response and "USD" in response:
                    coins[symbol] = {
                        "price": response["USD"],
                        "change_24h": 0  # از API دیگری دریافت می‌شود
                    }
            
            return coins
            
        except Exception as e:
            print(f"Error getting main coins prices: {e}")
            return {}
    
    @cache_result("trending_dex_tokens", ttl=180)  # 3 دقیقه کش
    async def get_trending_dex_tokens(self, limit: int = 20) -> List[Dict]:
        """دریافت توکن‌های ترند DEX با Redis Cache"""
        trending_tokens = []
        
        try:
            # استفاده از GeckoTerminal API
            url = f"{self.external_api_base}/api/geckoterminal/networks/solana/trending_pools"
            response = self._make_request(url)
            
            if "error" not in response and "pools" in response.get("data", {}):
                pools = response["data"]["pools"][:limit]
                
                for pool in pools:
                    attributes = pool.get("attributes", {})
                    token_data = attributes.get("base_token", {})
                    
                    trending_tokens.append({
                        "name": token_data.get("name", "Unknown"),
                        "symbol": token_data.get("symbol", "???"),
                        "address": token_data.get("address", ""),
                        "price": float(attributes.get("base_token_price_usd", 0)),
                        "price_change_24h": float(attributes.get("price_change_percentage", {}).get("h24", 0)),
                        "volume_24h": float(attributes.get("volume_usd", {}).get("h24", 0)),
                        "liquidity": float(attributes.get("reserve_in_usd", 0)),
                        "cached_at": datetime.now().isoformat()
                    })
            
            # اگر GeckoTerminal نتیجه نداد، از DexScreener استفاده کن
            if not trending_tokens:
                url = f"{self.external_api_base}/api/dexscreener/search"
                params = {"q": "solana"}
                response = self._make_request(url, params=params)
                
                if "error" not in response and "pairs" in response:
                    pairs = response["pairs"][:limit]
                    
                    for pair in pairs:
                        trending_tokens.append({
                            "name": pair.get("baseToken", {}).get("name", "Unknown"),
                            "symbol": pair.get("baseToken", {}).get("symbol", "???"),
                            "address": pair.get("baseToken", {}).get("address", ""),
                            "price": float(pair.get("priceUsd", 0)),
                            "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0)),
                            "volume_24h": float(pair.get("volume", {}).get("h24", 0)),
                            "liquidity": float(pair.get("liquidity", {}).get("usd", 0)),
                            "source": "DexScreener",
                            "cached_at": datetime.now().isoformat()
                        })
            
            return trending_tokens
            
        except Exception as e:
            print(f"Error getting trending tokens: {e}")
            return []
    
    @cache_result("top_coins", ttl=240)  # 4 دقیقه کش
    async def get_top_coins(self, limit: int = 10) -> List[Dict]:
        """دریافت کوین‌های برتر با Redis Cache"""
        try:
            # استفاده از CoinGecko search trending
            url = f"{self.external_api_base}/api/coingecko/search/trending"
            response = self._make_request(url)
            
            top_coins = []
            
            if "error" not in response and "coins" in response:
                coins = response["coins"][:limit]
                
                for i, coin_data in enumerate(coins):
                    item = coin_data.get("item", {})
                    
                    # دریافت قیمت هر کوین
                    price_url = f"{self.external_api_base}/api/cryptocompare/price"
                    price_params = {
                        "fsym": item.get("symbol", "BTC").upper(),
                        "tsyms": "USD"
                    }
                    price_response = self._make_request(price_url, params=price_params)
                    
                    price = 0
                    if "USD" in price_response:
                        price = price_response["USD"]
                    
                    top_coins.append({
                        "rank": i + 1,
                        "name": item.get("name", "Unknown"),
                        "symbol": item.get("symbol", "???").upper(),
                        "price": price,
                        "price_change_24h": item.get("price_btc", 0),
                        "market_cap": item.get("market_cap_rank", 0),
                        "volume_24h": 0,
                        "image": item.get("thumb", ""),
                        "cached_at": datetime.now().isoformat()
                    })
            
            return top_coins
            
        except Exception as e:
            print(f"Error getting top coins: {e}")
            return []
    
    @cache_result("token_analysis", ttl=600)  # 10 دقیقه کش برای تحلیل توکن
    async def analyze_token(self, token_address: str, chain: str = "solana") -> Dict:
        """تحلیل جامع یک توکن با Redis Cache"""
        result = {
            "basic_info": {},
            "price_data": {},
            "holder_analysis": {},
            "liquidity_info": {},
            "risk_analysis": {},
            "success": False,
            "cached_at": datetime.now().isoformat()
        }
        
        try:
            # اطلاعات پایه از GeckoTerminal
            url = f"{self.external_api_base}/api/geckoterminal/networks/solana/tokens/{token_address}/info"
            response = self._make_request(url)
            
            if "error" not in response and "data" in response:
                token_data = response.get("data", {}).get("attributes", {})
                
                result["basic_info"] = {
                    "name": token_data.get("name", "Unknown"),
                    "symbol": token_data.get("symbol", "???"),
                    "address": token_address,
                    "description": token_data.get("description", "")
                }
                
                result["price_data"] = {
                    "price_usd": float(token_data.get("price_usd", 0)),
                    "market_cap": float(token_data.get("market_cap_usd", 0))
                }
                
                result["success"] = True
            
            # اطلاعات از DexScreener
            url = f"{self.external_api_base}/api/dexscreener/tokens/solana/{token_address}"
            dex_response = self._make_request(url)
            
            if "error" not in dex_response and "pairs" in dex_response:
                pairs = dex_response.get("pairs", [])
                if pairs:
                    main_pair = pairs[0]
                    result["liquidity_info"] = {
                        "liquidity_usd": float(main_pair.get("liquidity", {}).get("usd", 0)),
                        "volume_24h": float(main_pair.get("volume", {}).get("h24", 0)),
                        "price_change_24h": float(main_pair.get("priceChange", {}).get("h24", 0))
                    }
            
            return result
            
        except Exception as e:
            print(f"Error analyzing token: {e}")
            result["error"] = str(e)
            return result
    
    # متدهای جدید برای endpoint های دیگر
    @cache_result("new_pairs", ttl=150)  # 2.5 دقیقه کش
    async def get_new_pairs(self, limit: int = 20) -> List[Dict]:
        """دریافت جفت‌های جدید با Redis Cache"""
        try:
            url = f"{self.external_api_base}/api/dexscreener/search"
            params = {"q": "solana"}
            response = self._make_request(url, params=params)
            
            new_pairs = []
            if "error" not in response and "pairs" in response:
                # مرتب‌سازی بر اساس زمان ایجاد
                pairs = sorted(response["pairs"], 
                             key=lambda x: x.get("pairCreatedAt", 0), 
                             reverse=True)[:limit]
                
                for pair in pairs:
                    new_pairs.append({
                        "name": pair.get("baseToken", {}).get("name", "Unknown"),
                        "symbol": pair.get("baseToken", {}).get("symbol", "???"),
                        "pair": f"{pair.get('baseToken', {}).get('symbol', '???')}/{pair.get('quoteToken', {}).get('symbol', 'USDT')}",
                        "created_at": pair.get("pairCreatedAt", ""),
                        "dex": pair.get("dexId", "Unknown"),
                        "liquidity": float(pair.get("liquidity", {}).get("usd", 0)),
                        "cached_at": datetime.now().isoformat()
                    })
            
            return new_pairs
            
        except Exception as e:
            print(f"Error getting new pairs: {e}")
            return []
    
    @cache_result("top_gainers", ttl=120)  # 2 دقیقه کش
    async def get_top_gainers(self, limit: int = 20) -> List[Dict]:
        """دریافت بیشترین رشدها با Redis Cache"""
        try:
            # ابتدا توکن‌های ترند رو می‌گیریم
            trending = await self.get_trending_dex_tokens(50)
            
            # مرتب‌سازی بر اساس تغییر قیمت 24 ساعته
            top_gainers = sorted(trending, 
                               key=lambda x: x.get("price_change_24h", 0), 
                               reverse=True)[:limit]
            
            # اضافه کردن timestamp برای tracking
            for gainer in top_gainers:
                gainer["cached_at"] = datetime.now().isoformat()
                gainer["category"] = "top_gainer"
            
            return top_gainers
            
        except Exception as e:
            print(f"Error getting top gainers: {e}")
            return []
    
    # Cache management methods
    def invalidate_market_cache(self):
        """پاک کردن کش‌های مربوط به بازار"""
        from utils.helpers import invalidate_cache_pattern
        
        patterns = [
            "market_overview:*",
            "main_coins_prices:*", 
            "trending_dex_tokens:*",
            "top_coins:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += invalidate_cache_pattern(pattern)
        
        print(f"🗑️ Invalidated {total_deleted} market cache entries")
        return total_deleted
    
    def invalidate_token_cache(self, token_address: str = None):
        """پاک کردن کش‌های مربوط به توکن خاص یا همه"""
        from utils.helpers import invalidate_cache_pattern
        
        if token_address:
            pattern = f"token_analysis:*{token_address}*"
        else:
            pattern = "token_analysis:*"
        
        deleted_count = invalidate_cache_pattern(pattern)
        print(f"🗑️ Invalidated {deleted_count} token cache entries")
        return deleted_count
    
    def get_cache_health(self):
        """بررسی سلامت کش‌ها"""
        from utils.helpers import get_cache_stats
        return get_cache_stats()

# نمونه global از سرویس
crypto_service = CryptoAPIService()
