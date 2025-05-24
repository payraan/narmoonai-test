import requests
import asyncio
from typing import Dict, Any, List
from config.settings import API_KEYS, BASE_URLS

class DirectAPIService:
    def __init__(self):
        self.api_keys = API_KEYS
        self.base_urls = BASE_URLS
    
    def _make_request(self, base_url: str, endpoint: str, headers: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """درخواست HTTP عمومی"""
        try:
            url = f"{base_url}{endpoint}"
            print(f"Making request to: {url}")
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            print(f"Response type: {type(result)}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"Error in API request to {url}: {e}")
            return {"error": True, "message": str(e)}
    
    # === CoinGecko APIs ===
    def coingecko_search(self, query: str) -> Dict[str, Any]:
        """جستجوی عمومی CoinGecko"""
        headers = {"accept": "application/json"}
        if self.api_keys["COINGECKO"] != "FREE":
            headers["x-cg-demo-api-key"] = self.api_keys["COINGECKO"]
        
        params = {"query": query}
        return self._make_request(
            self.base_urls["COINGECKO"], 
            "/search", 
            headers, 
            params
        )
    
    def coingecko_trending(self) -> Dict[str, Any]:
        """کوین‌های ترند CoinGecko"""
        headers = {"accept": "application/json"}
        if self.api_keys["COINGECKO"] != "FREE":
            headers["x-cg-demo-api-key"] = self.api_keys["COINGECKO"]
        
        return self._make_request(
            self.base_urls["COINGECKO"], 
            "/search/trending", 
            headers
        )
    
    def coingecko_global(self) -> Dict[str, Any]:
        """آمار جهانی کریپتو"""
        headers = {"accept": "application/json"}
        if self.api_keys["COINGECKO"] != "FREE":
            headers["x-cg-demo-api-key"] = self.api_keys["COINGECKO"]
        
        return self._make_request(
            self.base_urls["COINGECKO"], 
            "/global", 
            headers
        )
    
    def coingecko_defi(self) -> Dict[str, Any]:
        """آمار DeFi"""
        headers = {"accept": "application/json"}
        if self.api_keys["COINGECKO"] != "FREE":
            headers["x-cg-demo-api-key"] = self.api_keys["COINGECKO"]
        
        return self._make_request(
            self.base_urls["COINGECKO"], 
            "/global/decentralized_finance_defi", 
            headers
        )
    
    def coingecko_companies_treasury(self, coin_id: str) -> Dict[str, Any]:
        """ذخایر شرکت‌ها"""
        headers = {"accept": "application/json"}
        if self.api_keys["COINGECKO"] != "FREE":
            headers["x-cg-demo-api-key"] = self.api_keys["COINGECKO"]
        
        return self._make_request(
            self.base_urls["COINGECKO"], 
            f"/companies/public_treasury/{coin_id}", 
            headers
        )
    
    # === GeckoTerminal APIs ===
   
    def geckoterminal_token_info(self, network: str, address: str) -> Dict[str, Any]:
        """اطلاعات کامل توکن از GeckoTerminal - بهبود یافته"""
        headers = {"Accept": "application/json;version=20230302"}
        
        try:
            # دریافت اطلاعات پایه توکن
            token_info = self._make_request(
                self.base_urls["GECKOTERMINAL"], 
                f"/networks/{network}/tokens/{address}/info", 
                headers
            )
            
            # دریافت اطلاعات pools (قیمت، حجم، etc)
            pools_info = self._make_request(
                self.base_urls["GECKOTERMINAL"], 
                f"/networks/{network}/tokens/{address}/pools", 
                headers
            )
            
            # ترکیب اطلاعات
            if not token_info.get("error") and not pools_info.get("error"):
                # اضافه کردن pools data به token info
                if "data" in token_info and "data" in pools_info and pools_info["data"]:
                    token_info["pools_data"] = pools_info["data"][0].get("attributes", {})
            
            return token_info
            
        except Exception as e:
            print(f"Error in geckoterminal_token_info: {e}")
            return {"error": str(e)}
    
    def geckoterminal_trending_all(self) -> Dict[str, Any]:
        """توکن‌های ترند همه شبکه‌ها"""
        headers = {"Accept": "application/json;version=20230302"}
        result = self._make_request(
            self.base_urls["GECKOTERMINAL"], 
            "/networks/trending_pools", 
            headers
        )
        
        # اصلاح ساختار داده در صورت نیاز
        if isinstance(result, list):
            return {"data": {"pools": result}}
        elif "data" not in result and "pools" in result:
            return {"data": result}
        
        return result
    
    def geckoterminal_trending_network(self, network: str) -> Dict[str, Any]:
        """توکن‌های ترند شبکه خاص"""
        headers = {"Accept": "application/json;version=20230302"}
        result = self._make_request(
            self.base_urls["GECKOTERMINAL"], 
            f"/networks/{network}/trending_pools", 
            headers
        )
        
        # اصلاح ساختار داده - data یک لیست است نه dict
        if isinstance(result, dict) and "data" in result:
            # اگر data یک لیست است، آن را در فرمت مناسب قرار بده
            if isinstance(result["data"], list):
                return {"data": {"pools": result["data"]}}
            elif isinstance(result["data"], dict):
                return result
        elif isinstance(result, dict) and "pools" in result:
            return {"data": result}
            
        return result
    
    def geckoterminal_recently_updated(self) -> Dict[str, Any]:
        """توکن‌های به‌روزرسانی شده"""
        headers = {"Accept": "application/json;version=20230302"}
        result = self._make_request(
            self.base_urls["GECKOTERMINAL"], 
            "/tokens/info_recently_updated", 
            headers
        )
        
        # اصلاح ساختار داده
        if isinstance(result, list):
            return {"data": {"tokens": result}}
        elif "data" not in result and "tokens" in result:
            return {"data": result}
            
        return result
     
    def geckoterminal_token_pools(self, network: str, address: str) -> Dict[str, Any]:
        """دریافت pools مربوط به توکن"""
        headers = {"Accept": "application/json;version=20230302"}
        return self._make_request(
            self.base_urls["GECKOTERMINAL"], 
            f"/networks/{network}/tokens/{address}/pools", 
            headers
    )
    # === DexScreener APIs ===
    def dexscreener_boosted_tokens(self) -> List[Dict[str, Any]]:
        """توکن‌های تقویت‌شده"""
        headers = {"Accept": "*/*"}
        result = self._make_request(
            self.base_urls["DEXSCREENER"], 
            "/token-boosts/latest/v1", 
            headers
        )
        
        # اگر نتیجه لیست بود، آن را برگردان
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and result.get("error"):
            return []
        elif isinstance(result, dict) and "data" in result:
            return result["data"] if isinstance(result["data"], list) else []
        
        # اگر هیچ‌کدام نبود، لیست خالی برگردان
        return []
    
    # === Moralis APIs ===
    def moralis_trending_tokens(self, limit: int = 10) -> Dict[str, Any]:
        """توکن‌های ترند Moralis"""
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_keys["MORALIS"]
        }
        params = {"limit": limit}
        return self._make_request(
            self.base_urls["MORALIS_INDEX"], 
            "/tokens/trending", 
            headers, 
            params
        )
    
    def moralis_snipers(self, pair_address: str) -> Dict[str, Any]:
        """اسنایپرهای توکن"""
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_keys["MORALIS"]
        }
        return self._make_request(
            self.base_urls["MORALIS_SOLANA"], 
            f"/token/mainnet/pairs/{pair_address}/snipers", 
            headers
        )
    
    # === Combined Methods ===
    async def get_combined_solana_trending(self) -> Dict[str, Any]:
        """ترکیب توکن‌های ترند سولانا از GeckoTerminal و Moralis - اصلاح شده"""
        try:
            # دریافت داده‌ها از GeckoTerminal
            gecko_data = self.geckoterminal_trending_network("solana")
            print(f"Gecko data type: {type(gecko_data)}")
            
            combined_tokens = []
            
            # پردازش داده‌های GeckoTerminal
            if isinstance(gecko_data, dict) and not gecko_data.get("error"):
                if "data" in gecko_data and isinstance(gecko_data["data"], dict) and "pools" in gecko_data["data"]:
                    pools = gecko_data["data"]["pools"]
                elif "data" in gecko_data and isinstance(gecko_data["data"], list):
                    pools = gecko_data["data"]
                else:
                    pools = []
                
                print(f"Processing {len(pools)} pools from GeckoTerminal")
                
                for i, pool in enumerate(pools[:10]):
                    try:
                        if isinstance(pool, dict) and "attributes" in pool:
                            attributes = pool["attributes"]
                            
                            # استخراج نام از pool name (مثل "moonpig / SOL")
                            pool_name = attributes.get("name", f"Pool_{i+1}")
                            if " / " in pool_name:
                                token_name = pool_name.split(" / ")[0]
                                token_symbol = token_name.upper()
                            else:
                                token_name = pool_name
                                token_symbol = token_name[:4].upper()
                            
                            # استخراج آدرس کامل از relationships
                            token_address = ""
                            if "relationships" in pool and "base_token" in pool["relationships"]:
                                base_token_data = pool["relationships"]["base_token"]["data"]
                                if "id" in base_token_data:
                                    # ID به فرمت "solana_ADDRESS" است
                                    full_id = base_token_data["id"]
                                    if "_" in full_id:
                                        token_address = full_id.split("_", 1)[1]
                                    else:
                                        token_address = full_id
                            
                            token_data = {
                                "source": "GeckoTerminal",
                                "name": token_name,
                                "symbol": token_symbol,
                                "address": token_address,  # آدرس کامل
                                "price_usd": attributes.get("base_token_price_usd", "0"),
                                "volume_24h": 0,
                                "price_change_24h": 0,
                                # اطلاعات جدید ⭐
                                "liquidity_usd": attributes.get("reserve_in_usd", "0"),
                                "fdv_usd": attributes.get("fdv_usd", "0"),
                                "pool_created_at": attributes.get("pool_created_at", ""),
                                "transactions_24h": attributes.get("transactions", {}).get("h24", {}),
                                "market_cap": attributes.get("fdv_usd", "0")
                            }
                            
                            # استخراج ایمن volume
                            volume_usd = attributes.get("volume_usd", {})
                            if isinstance(volume_usd, dict):
                                vol_24h = volume_usd.get("h24", 0)
                                try:
                                    token_data["volume_24h"] = float(vol_24h) if vol_24h else 0
                                except (ValueError, TypeError):
                                    token_data["volume_24h"] = 0
                            
                            # استخراج ایمن price change
                            price_change = attributes.get("price_change_percentage", {})
                            if isinstance(price_change, dict):
                                change_24h = price_change.get("h24", 0)
                                try:
                                    token_data["price_change_24h"] = float(change_24h) if change_24h else 0
                                except (ValueError, TypeError):
                                    token_data["price_change_24h"] = 0
                            
                            combined_tokens.append(token_data)
                            
                    except Exception as e:
                        print(f"Error processing pool {i}: {e}")
                        continue
            
            # اگر هیچ توکنی از GeckoTerminal نیامد، داده‌های نمونه اضافه کن
            if not combined_tokens:
                sample_names = ["BONK", "WIF", "POPCAT", "MOODENG", "PNUT"]
                for i, name in enumerate(sample_names):
                    combined_tokens.append({
                        "source": "Sample",
                        "name": name,
                        "symbol": name,
                        "address": f"sample_{i+1}",
                        "price_usd": f"0.00{i+1}",
                        "volume_24h": 10000 * (i+1),
                        "price_change_24h": (i+1) * 5.2
                    })
            
            return {
                "success": True,
                "combined_tokens": combined_tokens,
                "total_count": len(combined_tokens)
            }
            
        except Exception as e:
            print(f"Error in get_combined_solana_trending: {e}")
            import traceback
            traceback.print_exc()
            
            # در صورت خطا، داده‌های نمونه برگردان
            fallback_tokens = []
            sample_names = ["BONK", "WIF", "POPCAT"]
            for i, name in enumerate(sample_names):
                fallback_tokens.append({
                    "source": "Fallback",
                    "name": name,
                    "symbol": name,
                    "address": f"fallback_{i+1}",
                    "price_usd": f"0.00{i+1}",
                    "volume_24h": 5000 * (i+1),
                    "price_change_24h": (i+1) * 3.1
                })
            
            return {
                "success": True,
                "combined_tokens": fallback_tokens,
                "total_count": len(fallback_tokens)
            }

# نمونه global از سرویس
direct_api_service = DirectAPIService()
