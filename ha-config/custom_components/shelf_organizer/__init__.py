# /config/custom_components/shelf_organizer/__init__.py

"""Shelf Organizer integration."""
import logging
import aiohttp
import async_timeout
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN = "shelf_organizer"
LLM_HOST = "192.168.0.215"  # Your AMD machine IP
LLM_PORT = 28080
SCAN_INTERVAL = timedelta(seconds=30)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Shelf Organizer integration."""
    hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Shelf Organizer from a config entry."""
    
    # Store LLM client
    hass.data[DOMAIN]["client"] = ShelfOrganizerClient(
        hass,
        entry.data.get("host", LLM_HOST),
        entry.data.get("port", LLM_PORT)
    )
    
    # Register services
    async def handle_query(call):
        """Handle inventory query service."""
        client = hass.data[DOMAIN]["client"]
        query = call.data.get("query")
        intent = call.data.get("intent", "general")
        
        result = await client.query_llm(query, intent)
        return result
    
    hass.services.async_register(DOMAIN, "query", handle_query)
    
    return True

class ShelfOrganizerClient:
    """Client for LLM server."""
    
    def __init__(self, hass, host, port):
        self.hass = hass
        self.host = host
        self.port = port
        self.session = async_get_clientsession(hass)
    
    async def query_llm(self, query: str, intent: str = "general"):
        """Send query to LLM server."""
        url = f"http://{self.host}:{self.port}/query"
        
        try:
            async with async_timeout.timeout(10):
                async with self.session.post(
                    url,
                    json={"query": query, "intent": intent}
                ) as response:
                    result = await response.json()
                    return result
        except Exception as e:
            _LOGGER.error(f"Failed to query LLM: {e}")
            return {
                "success": False,
                "spoken": "Sorry, I couldn't connect to the inventory system"
            }
