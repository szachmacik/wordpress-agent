"""
Task Processor - nasłuchuje zadań w Supabase i wykonuje je autonomicznie
"""
import asyncio
import logging
from typing import Dict, List
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)

class TaskProcessor:
    def __init__(self, wp_client, claude_planner, notifier, supabase_url: str, supabase_key: str):
        self.wp_client = wp_client
        self.claude_planner = claude_planner
        self.notifier = notifier
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.is_running = False
        self.poll_interval = 10  # seconds
        
        self.stats = {
            "tasks_processed": 0,
            "tasks_failed": 0,
            "operations_executed": 0,
            "started_at": None
        }
    
    async def start(self):
        """Start task processing loop"""
        self.is_running = True
        self.stats["started_at"] = datetime.now().isoformat()
        
        logger.info("🎯 Task processor started - polling Supabase every 10s")
        await self.notifier.send("🤖 WordPress Agent uruchomiony!")
        
        while self.is_running:
            try:
                await self.process_pending_tasks()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in task loop: {e}")
                await asyncio.sleep(self.poll_interval)
    
    async def stop(self):
        """Stop task processing"""
        self.is_running = False
        logger.info("🛑 Task processor stopped")
    
    async def process_pending_tasks(self):
        """Fetch and process pending tasks from Supabase"""
        try:
            # Get pending tasks
            tasks = await self.fetch_pending_tasks()
            
            if not tasks:
                return
            
            logger.info(f"📋 Found {len(tasks)} pending tasks")
            
            for task in tasks:
                try:
                    await self.process_task(task)
                except Exception as e:
                    logger.error(f"Task {task['id']} failed: {e}")
                    await self.mark_task_failed(task['id'], str(e))
                    self.stats["tasks_failed"] += 1
        
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
    
    async def fetch_pending_tasks(self) -> List[Dict]:
        """Fetch pending WordPress tasks from Supabase"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.supabase_url}/rest/v1/wp_agent_tasks",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}"
                },
                params={
                    "status": "eq.pending",
                    "order": "created_at.asc",
                    "limit": "5"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch tasks: {response.status_code}")
                return []
    
    async def process_task(self, task: Dict):
        """Process a single task"""
        task_id = task['id']
        description = task['description']
        
        logger.info(f"🚀 Processing task {task_id}: {description}")
        
        # Mark as processing
        await self.mark_task_processing(task_id)
        
        # Notify start
        await self.notifier.send(f"⏳ Rozpoczynam: {description}")
        
        # Get plan from Claude
        plan = await self.claude_planner.plan_operations(
            description, 
            self.wp_client.url
        )
        
        if "error" in plan:
            raise Exception(plan["error"])
        
        # Execute operations
        results = []
        for operation in plan["operations"]:
            try:
                result = await self.execute_operation(operation)
                results.append({
                    "operation": operation["description"],
                    "success": True,
                    "result": str(result)[:200]  # Limit result size
                })
                self.stats["operations_executed"] += 1
                logger.info(f"✅ {operation['description']}")
            except Exception as e:
                results.append({
                    "operation": operation["description"],
                    "success": False,
                    "error": str(e)
                })
                logger.error(f"❌ {operation['description']}: {e}")
        
        # Mark as completed
        await self.mark_task_completed(task_id, plan["summary"], results)
        self.stats["tasks_processed"] += 1
        
        # Notify completion
        success_count = sum(1 for r in results if r["success"])
        await self.notifier.send(
            f"✅ Ukończono: {description}\n"
            f"Operacji: {success_count}/{len(results)}\n"
            f"{plan['summary']}"
        )
    
    async def execute_operation(self, operation: Dict):
        """Execute a single WordPress operation"""
        endpoint = operation["endpoint"]
        method = operation["method"].upper()
        data = operation.get("data")
        
        if method == "GET":
            return await self.wp_client.get(endpoint)
        elif method == "POST":
            return await self.wp_client.post(endpoint, data)
        elif method == "PUT":
            return await self.wp_client.put(endpoint, data)
        elif method == "DELETE":
            return await self.wp_client.delete(endpoint)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    async def mark_task_processing(self, task_id: str):
        """Mark task as processing in Supabase"""
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"{self.supabase_url}/rest/v1/wp_agent_tasks?id=eq.{task_id}",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "status": "processing",
                    "started_at": datetime.now().isoformat()
                }
            )
    
    async def mark_task_completed(self, task_id: str, summary: str, results: List[Dict]):
        """Mark task as completed in Supabase"""
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"{self.supabase_url}/rest/v1/wp_agent_tasks?id=eq.{task_id}",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "status": "completed",
                    "completed_at": datetime.now().isoformat(),
                    "summary": summary,
                    "results": results
                }
            )
    
    async def mark_task_failed(self, task_id: str, error: str):
        """Mark task as failed in Supabase"""
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"{self.supabase_url}/rest/v1/wp_agent_tasks?id=eq.{task_id}",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "status": "failed",
                    "completed_at": datetime.now().isoformat(),
                    "error": error
                }
            )
    
    async def create_task(self, description: str) -> str:
        """Create a new task (for manual/API usage)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.supabase_url}/rest/v1/wp_agent_tasks",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                },
                json={
                    "description": description,
                    "status": "pending",
                    "created_at": datetime.now().isoformat()
                }
            )
            
            task = response.json()[0]
            return task["id"]
    
    async def get_stats(self) -> Dict:
        """Get agent statistics"""
        return self.stats
