# /config/custom_components/shelf_organizer/__init__.py

"""Shelf Organizer integration."""
import logging
import aiohttp
import async_timeout
from datetime import timedelta

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .intent import (
  FindItemIntentHandler,
  ListContainerIntentHandler, 
  AddItemIntentHandler,
  FindSpaceIntentHandler
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "shelf_organizer"
LLM_HOST = "192.168.0.215"  # Your AMD machine IP
LLM_PORT = 28080

async def async_setup(hass: HomeAssistant, config: dict):
  """Set up the Shelf Organizer integration."""
  
  # Initialize domain data
  hass.data[DOMAIN] = {}
  
  # Create LLM client
  client = ShelfOrganizerClient(hass, LLM_HOST, LLM_PORT)
  hass.data[DOMAIN]["client"] = client
  
  # Register service/action
  async def handleQuery(call: ServiceCall):
    """Handle inventory query service."""
    query = call.data.get("query")
    intent = call.data.get("intent", "general")
    
    _LOGGER.debug(f"Received query: {query}, intent: {intent}")
    result = await client.queryLlm(query, intent)
    _LOGGER.debug(f"LLM result: {result}")
    
    # Register intent handlers
    intent.async_register(hass, FindItemIntentHandler())
    intent.async_register(hass, ListContainerIntentHandler())
    intent.async_register(hass, AddItemIntentHandler())
    intent.async_register(hass, FindSpaceIntentHandler())
    _LOGGER.info("Shelf Organizer intent handlers registered")

    return result
  
  hass.services.async_register(DOMAIN, "query", handleQuery)
  _LOGGER.info("Shelf Organizer service registered successfully")
  
  return True


class ShelfOrganizerClient:
  """Client for LLM server."""
  
  def __init__(self, hass, host, port):
    self.hass = hass
    self.host = host
    self.port = port
    self.session = async_get_clientsession(hass)
  
  async def queryLlm(self, query: str, intent: str = "general"):
    """Send query to LLM server."""
    url = f"http://{self.host}:{self.port}/query"
    
    _LOGGER.debug(f"Sending to {url}: query={query}, intent={intent}")
    
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
