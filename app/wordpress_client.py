"""
WordPress REST API Client
"""
import httpx
import logging
from typing import Dict, List, Optional, Any
from base64 import b64encode

logger = logging.getLogger(__name__)

class WordPressClient:
    def __init__(self, url: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.api_base = f"{self.url}/wp-json/wp/v2"
        
        # Create auth header
        credentials = f"{username}:{password}"
        token = b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json"
        }
    
    async def test_connection(self) -> bool:
        """Test WordPress connection"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/posts?per_page=1",
                    headers=self.headers,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """GET request to WordPress API"""
        url = f"{self.api_base}{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def post(self, endpoint: str, data: Dict) -> Any:
        """POST request to WordPress API"""
        url = f"{self.api_base}{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=data, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def put(self, endpoint: str, data: Dict) -> Any:
        """PUT request to WordPress API"""
        url = f"{self.api_base}{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.put(url, headers=self.headers, json=data, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    async def delete(self, endpoint: str) -> Any:
        """DELETE request to WordPress API"""
        url = f"{self.api_base}{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    # Convenience methods
    async def list_posts(self, per_page: int = 10, status: str = "any") -> List[Dict]:
        """List WordPress posts"""
        return await self.get("/posts", {"per_page": per_page, "status": status})
    
    async def get_post(self, post_id: int) -> Dict:
        """Get single post"""
        return await self.get(f"/posts/{post_id}")
    
    async def create_post(self, title: str, content: str, status: str = "draft") -> Dict:
        """Create new post"""
        data = {
            "title": title,
            "content": content,
            "status": status
        }
        return await self.post("/posts", data)
    
    async def update_post(self, post_id: int, **kwargs) -> Dict:
        """Update post"""
        return await self.put(f"/posts/{post_id}", kwargs)
    
    async def delete_post(self, post_id: int) -> Dict:
        """Delete post"""
        return await self.delete(f"/posts/{post_id}")
    
    async def list_pages(self, per_page: int = 10) -> List[Dict]:
        """List WordPress pages"""
        return await self.get("/pages", {"per_page": per_page})
    
    async def list_categories(self) -> List[Dict]:
        """List categories"""
        return await self.get("/categories")
    
    async def list_tags(self) -> List[Dict]:
        """List tags"""
        return await self.get("/tags")
    
    async def list_media(self, per_page: int = 10) -> List[Dict]:
        """List media items"""
        return await self.get("/media", {"per_page": per_page})
