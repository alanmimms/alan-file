#!/bin/bash
# fix-shelf-llm.sh

echo "Setting up shelf-llm-server..."

# Create directory
mkdir -p ~/shelf-llm-server
cd ~/shelf-llm-server

# Remove old venv if it exists
if [ -d "venv" ]; then
    echo "Removing old venv..."
    rm -rf venv
fi

# Create fresh virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install aiohttp

# Create a simple test server first
echo "Creating server.py..."
cat > server.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import json
import logging
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShelfLLMServer:
    def __init__(self):
        logger.info("Initializing Shelf LLM Server...")
        self.model = "qwen2.5:3b"  # Adjust to your model
        
    async def process_query(self, request):
        """Handle incoming queries from Home Assistant"""
        try:
            data = await request.json()
            query = data.get('query', '')
            
            logger.info(f"Received query: {query}")
            
            # For now, just echo back to test
            return web.json_response({
                'success': True,
                'response': f"Received: {query}",
                'spoken': f"I heard: {query}"
            })
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return web.json_response({
                'success': False,
                'error': str(e)
            })
    
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'model': self.model
        })

def create_app():
    app = web.Application()
    server = ShelfLLMServer()
    
    app.router.add_post('/query', server.process_query)
    app.router.add_get('/health', server.health_check)
    
    return app

if __name__ == '__main__':
    logger.info("Starting server on port 28080...")
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=28080)
EOF

# Make sure it's executable (though not needed for python)
chmod +x server.py

# Test that it runs directly
echo "Testing direct execution..."
timeout 5 ./venv/bin/python server.py || true

# Stop any existing service
systemctl --user stop shelf-llm.service 2>/dev/null || true

# Update the service file
echo "Creating systemd service..."
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/shelf-llm.service << 'EOF'
[Unit]
Description=Shelf Organizer LLM Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/alan/shelf-llm-server
ExecStart=/home/alan/shelf-llm-server/venv/bin/python /home/alan/shelf-llm-server/server.py
Restart=always
RestartSec=5
RestartPreventExitStatus=0

Environment="OLLAMA_HOST=localhost:11434"
Environment="OLLAMA_KEEP_ALIVE=24h"
Environment="OLLAMA_NUM_GPU=99"

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

# Reload and start
echo "Starting service..."
systemctl --user daemon-reload
systemctl --user enable shelf-llm.service
systemctl --user restart shelf-llm.service

# Wait a moment
sleep 2

# Check status
echo "Checking service status..."
systemctl --user status shelf-llm.service --no-pager

# Test the endpoint
echo "Testing endpoint..."
curl -s http://localhost:28080/health | python3 -m json.tool

echo "Done! Check logs with: journalctl --user -u shelf-llm -f"
