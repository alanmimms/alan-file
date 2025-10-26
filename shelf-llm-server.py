#!/usr/bin/env python3
# /home/alan/shelf-llm-server/server.py

import asyncio
import json
import logging
from aiohttp import web
import subprocess
import time
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShelfLLMServer:
    def __init__(self):
        self.model = "qwen2.5:3b-instruct-q4_K_M"  # Or your preferred model
        self.last_query = time.time()
        
        # Ensure model is loaded at startup
        self.warmup_model()
        
    def warmup_model(self):
        """Pre-load model into memory"""
        logger.info(f"Loading {self.model} into memory...")
        try:
            result = subprocess.run(
                ["ollama", "run", self.model],
                input="test",
                capture_output=True,
                text=True,
                timeout=30
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
    
    async def process_query(self, request):
        """Handle incoming queries from Home Assistant"""
        try:
            data = await request.json()
            query = data.get('query', '')
            intent = data.get('intent', '')
            
            logger.info(f"Received query: {query}, intent: {intent}")
            
            # Build prompt based on intent type
            prompt = self.build_prompt(query, intent)
            
            # Run through Ollama
            result = await self.run_ollama(prompt)
            
            # Parse LLM response
            response = self.parse_response(result, intent)
            
            self.last_query = time.time()
            
            return web.json_response({
                'success': True,
                'response': response,
                'spoken': response.get('spoken_text', 'I processed your request')
            })
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return web.json_response({
                'success': False,
                'error': str(e),
                'spoken': 'Sorry, I encountered an error'
            })
    
    def build_prompt(self, query: str, intent: str) -> str:
        """Build appropriate prompt based on intent"""
        
        base_prompt = """You are an electronics inventory assistant managing a shelf/drawer organization system.

Containers use format: "drawer 3.5" (cabinet.drawer) or "shelf 1.3" (unit.shelf)
Positions: northwest, north, northeast, west, center, east, southwest, south, southeast
Components: Parse "47k" as "47k resistor", "2.2uF" as "2.2 microfarad capacitor", etc.

Current query: "{query}"
Intent type: {intent}

Respond with JSON including a 'spoken_text' field for voice response.
"""
        
        intent_prompts = {
            'find_item': """Find the requested item and return:
{
  "action": "find",
  "item": "item description",
  "locations": [{"container": "drawer 3.5", "position": "northwest", "quantity": 25}],
  "spoken_text": "I found [item] in [location]"
}""",
            
            'add_item': """Parse the add request and return:
{
  "action": "add",
  "item": "item description",
  "container": "drawer 3.5",
  "position": "northwest",
  "quantity": 1,
  "spoken_text": "Added [item] to [location]"
}""",
            
            'list_container': """List container contents:
{
  "action": "list",
  "container": "drawer 3.5",
  "contents": [{"position": "north", "item": "47k resistors", "quantity": 25}],
  "spoken_text": "Drawer 3.5 contains: [list of items]"
}""",
            
            'find_space': """Find available space:
{
  "action": "find_space",
  "dimensions": {"width": 10, "depth": 5, "height": 3},
  "available_locations": [{"container": "shelf 2.1", "positions": ["south", "southeast"]}],
  "spoken_text": "I found space in [location]"
}"""
        }
        
        specific_prompt = intent_prompts.get(intent, "Parse the query and respond appropriately.")
        
        return base_prompt.format(query=query, intent=intent) + "\n\n" + specific_prompt
    
    async def run_ollama(self, prompt: str) -> str:
        """Run Ollama asynchronously"""
        process = await asyncio.create_subprocess_exec(
            'ollama', 'run', self.model,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate(prompt.encode())
        
        if process.returncode != 0:
            raise Exception(f"Ollama failed: {stderr.decode()}")
        
        return stdout.decode()
    
    def parse_response(self, llm_output: str, intent: str) -> Dict[str, Any]:
        """Parse LLM output to structured response"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', llm_output, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                # Fallback to text response
                return {
                    'action': intent,
                    'spoken_text': llm_output.strip()
                }
                
        except Exception as e:
            logger.error(f"Failed to parse LLM output: {e}")
            return {
                'action': intent,
                'spoken_text': llm_output.strip()[:200]  # Limit length
            }
    
    async def health_check(self, request):
        """Health check endpoint for HA to verify service is up"""
        return web.json_response({
            'status': 'healthy',
            'model': self.model,
            'last_query': time.time() - self.last_query
        })

def create_app():
    app = web.Application()
    server = ShelfLLMServer()
    
    app.router.add_post('/query', server.process_query)
    app.router.add_get('/health', server.health_check)
    
    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=28080)
