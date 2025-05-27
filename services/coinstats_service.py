import requests
from typing import Dict, Any
from datetime import datetime
from config.settings import API_KEYS, BASE_URLS
from utils.helpers import cache_result

class CoinStatsService:
    def __init__(self):
        self.api_key = API_KEYS.get("COINSTATS", "")
        self.base_url = BASE_URLS["COINSTATS"]
        
    @cache_result("btc_dominance", ttl=300)  # 5 دقیقه کش
    def get_btc_dominance(self) -> Dict[str, Any]:
        """دریافت دامیننس بیتکوین از CoinGecko (رایگان و لایو)"""
        try:
            url = "https://api.coingecko.com/api/v3/global"
            headers = {"accept": "application/json"}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "data" in data:
                btc_dominance = data["data"].get("market_cap_percentage", {}).get("btc", 0)
                return {
                    "btcDominance": btc_dominance,
                    "timestamp": "live",
                    "source": "CoinGecko",
                    "cached_at": datetime.now().isoformat()
                }
            
        except Exception as e:
            print(f"Error getting BTC dominance: {e}")
        
        # fallback data اگر API کار نکرد
        return {
            "btcDominance": 60.5,
            "timestamp": "fallback",
            "source": "fallback",
            "cached_at": datetime.now().isoformat()
        }
    
    @cache_result("fear_greed", ttl=300)  # 5 دقیقه کش
    def get_fear_and_greed(self) -> Dict[str, Any]:
        """دریافت شاخص ترس و طمع از Fear and Greed Index API"""
        try:
            # API رایگان Fear & Greed Index
            url = "https://api.alternative.me/fng/"
            headers = {"accept": "application/json"}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "data" in data and data["data"]:
                fng_data = data["data"][0]
                value = int(fng_data.get("value", 50))
                classification = fng_data.get("value_classification", "Neutral")
                
                return {
                    "value": value,
                    "valueClassification": classification,
                    "timestamp": "live",
                    "source": "Alternative.me",
                    "cached_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"Error getting Fear & Greed: {e}")
        
        # fallback data
        return {
            "value": 65,
            "valueClassification": "Greed",
            "timestamp": "fallback",
            "source": "fallback",
            "cached_at": datetime.now().isoformat()
        }

# نمونه global از سرویس
coinstats_service = CoinStatsService()
