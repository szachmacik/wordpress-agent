"""
Claude Planner - używa Claude API do planowania operacji WordPress
"""
import httpx
import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class ClaudePlanner:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"
    
    async def plan_operations(self, task_description: str, wp_url: str) -> Dict:
        """
        Używa Claude do zaplanowania operacji WordPress dla zadania
        
        Returns:
            {
                "operations": [
                    {
                        "endpoint": "/posts",
                        "method": "GET/POST/PUT/DELETE",
                        "data": {...},
                        "description": "Co robi ta operacja"
                    }
                ],
                "summary": "Podsumowanie co zostanie zrobione"
            }
        """
        
        system_prompt = f"""Jesteś autonomicznym agentem WordPress. Masz dostęp do WordPress REST API.

URL: {wp_url}
Możesz wykonywać operacje na:
- Postach (/posts) - tworzenie, edycja, usuwanie
- Stronach (/pages)
- Mediach (/media)
- Kategoriach (/categories)
- Tagach (/tags)

Użytkownik prosi: {task_description}

Zwróć TYLKO JSON z instrukcjami jakie operacje API muszę wykonać. Format:
{{
  "operations": [
    {{
      "endpoint": "/posts",
      "method": "GET",
      "data": null,
      "description": "Pobierz listę postów"
    }},
    {{
      "endpoint": "/posts",
      "method": "POST",
      "data": {{"title": "Tytuł", "content": "Treść", "status": "draft"}},
      "description": "Utwórz nowy draft"
    }}
  ],
  "summary": "Wykonam X operacji: ..."
}}

WAŻNE:
- Zwróć TYLKO JSON, bez żadnego tekstu przed ani po
- Każda operacja musi mieć: endpoint, method, data (lub null), description
- Dla POST/PUT podaj konkretne dane w polu "data"
- Dla GET endpoint może zawierać query params, np: "/posts?status=draft&per_page=5"
"""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 4000,
                        "messages": [
                            {
                                "role": "user",
                                "content": system_prompt
                            }
                        ]
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract text from response
                text_blocks = [block for block in data["content"] if block["type"] == "text"]
                response_text = "\n".join(block["text"] for block in text_blocks)
                
                # Parse JSON from response
                # Find JSON in the response (might be wrapped in markdown code blocks)
                response_text = response_text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text.split("```json")[1]
                    response_text = response_text.split("```")[0]
                elif response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    response_text = response_text.split("```")[0]
                
                plan = json.loads(response_text.strip())
                
                logger.info(f"✅ Claude plan: {plan['summary']}")
                return plan
                
        except Exception as e:
            logger.error(f"❌ Claude planning failed: {e}")
            # Fallback - return simple plan
            return {
                "operations": [],
                "summary": f"Błąd planowania: {str(e)}",
                "error": str(e)
            }
