import requests
import time
from config.settings import API_KEYS, BASE_URLS

class HolderScanService:
    def __init__(self):
        self.api_key = API_KEYS.get("HOLDERSCAN", "FREE")
        self.base_url = "https://api.holderscan.com/v0"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        # اضافه کردن API key
        if self.api_key and self.api_key != "FREE":
            self.headers["X-API-KEY"] = self.api_key
            print(f"HolderScan API Key loaded: {self.api_key[:10]}...")
    
    def _make_request(self, endpoint, params=None):
        """درخواست HTTP عمومی"""
        try:
            url = f"{self.base_url}{endpoint}"
            print(f"Making HolderScan request to: {url}")
            print(f"Headers: {self.headers}")
            if params:
                print(f"Params: {params}")
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            print(f"HolderScan Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response data preview: {str(data)[:200]}...")
                return data
            elif response.status_code == 429:
                retry_after = response.headers.get('Retry-After', 'N/A')
                return {"error": f"Rate limit exceeded. Retry after: {retry_after}s", "status_code": 429}
            elif response.status_code == 401:
                return {"error": "Invalid or missing API key", "status_code": 401}
            elif response.status_code == 404:
                return {"error": "Token not found or not supported", "status_code": 404}
            else:
                return {
                    "error": f"HTTP {response.status_code}", 
                    "status_code": response.status_code, 
                    "response": response.text[:500]
                }
                
        except requests.exceptions.Timeout:
            return {"error": "Request timeout after 30 seconds"}
        except requests.exceptions.ConnectionError:
            return {"error": "Connection error - check internet connection"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except ValueError as e:
            return {"error": f"Invalid JSON response: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def token_holders(self, contract_address, chain_id="sol", limit=50, offset=0):
        """
        لیست صفحه‌بندی شده هولدرهای توکن
        Request units: 10
        """
        endpoint = f"/{chain_id}/tokens/{contract_address}/holders"
        params = {
            "limit": min(limit, 100),  # حداکثر 100
            "offset": offset
        }
        return self._make_request(endpoint, params)
    
    def token_stats(self, contract_address, chain_id="sol"):
        """
        آمار تجمیعی توکن شامل تمرکز و توزیع
        Request units: 20
        """
        endpoint = f"/{chain_id}/tokens/{contract_address}/stats"
        return self._make_request(endpoint)
    
    def holder_deltas(self, contract_address, chain_id="sol"):
        """
        تغییرات هولدرها در بازه‌های زمانی مختلف
        Request units: 20
        """
        endpoint = f"/{chain_id}/tokens/{contract_address}/holders/deltas"
        return self._make_request(endpoint)
    
    def holder_breakdowns(self, contract_address, chain_id="sol"):
        """
        آمار هولدرها بر اساس ارزش نگهداری
        Request units: 50
        """
        endpoint = f"/{chain_id}/tokens/{contract_address}/holders/breakdowns"
        return self._make_request(endpoint)
    
    def token_details(self, contract_address, chain_id="sol"):
        """
        جزئیات یک توکن خاص
        Request units: 10
        """
        endpoint = f"/{chain_id}/tokens/{contract_address}"
        return self._make_request(endpoint)
    
    def list_tokens(self, chain_id="sol", limit=50, offset=0):
        """
        لیست توکن‌های پشتیبانی شده
        Request units: 10
        """
        endpoint = f"/{chain_id}/tokens"
        params = {
            "limit": min(limit, 100),
            "offset": offset
        }
        return self._make_request(endpoint)
    
    def test_connection(self):
        """
        تست اتصال و API key
        """
        print("\n=== Testing HolderScan Connection ===")
        # تست با یک توکن معروف سولانا (USDC)
        test_token = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        result = self.token_details(test_token)
        
        if not result.get("error"):
            print("✅ Connection successful!")
            print(f"Token found: {result.get('name')} ({result.get('ticker')})")
            return True
        else:
            print(f"❌ Connection failed: {result.get('error')}")
            return False

    def get_popular_tokens():
     """لیست توکن‌های محبوب سولانا که توسط HolderScan پشتیبانی می‌شوند"""
     return {
        "BONK": {
            "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "name": "Bonk"
        },
        "WIF": {
            "address": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm", 
            "name": "dogwifhat"
        },
        "JUP": {
            "address": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
            "name": "Jupiter"
        },
        "PYTH": {
            "address": "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3",
            "name": "Pyth Network"
        },
        "ORCA": {
            "address": "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE",
            "name": "Orca"
        }
    }

# نمونه global
holderscan_service = HolderScanService()
