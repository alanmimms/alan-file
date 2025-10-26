# /config/custom_components/shelf_organizer/intent.py

"""Intent handlers for Shelf Organizer."""
import logging
from homeassistant.helpers import intent
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

DOMAIN = "shelf_organizer"

class FindItemIntentHandler(intent.IntentHandler):
  """Handle FindItem intent."""
  
  intent_type = "FindItem"
  slot_schema = {
    "item_description": cv.string
  }
  
  async def async_handle(self, intentObj):
    """Handle the intent."""
    hass = intentObj.hass
    slots = intentObj.slots
    
    itemDesc = slots.get("item_description", {}).get("value", "")
    _LOGGER.debug(f"FindItem intent triggered for: {itemDesc}")
    
    # Call the query service
    client = hass.data[DOMAIN]["client"]
    result = await client.queryLlm(itemDesc, "find_item")
    
    response = intentObj.create_response()
    spokenText = result.get("spoken", "I couldn't find that item")
    response.async_set_speech(spokenText)
    
    return response


class ListContainerIntentHandler(intent.IntentHandler):
  """Handle ListContainer intent."""
  
  intent_type = "ListContainer"
  slot_schema = {
    "container": cv.string
  }
  
  async def async_handle(self, intentObj):
    """Handle the intent."""
    hass = intentObj.hass
    slots = intentObj.slots
    
    container = slots.get("container", {}).get("value", "")
    _LOGGER.debug(f"ListContainer intent triggered for: {container}")
    
    client = hass.data[DOMAIN]["client"]
    result = await client.queryLlm(f"list {container}", "list_container")
    
    response = intentObj.create_response()
    spokenText = result.get("spoken", "I couldn't access that container")
    response.async_set_speech(spokenText)
    
    return response


class AddItemIntentHandler(intent.IntentHandler):
  """Handle AddItem intent."""
  
  intent_type = "AddItem"
  slot_schema = {
    "item_description": cv.string,
    "location": cv.string
  }
  
  async def async_handle(self, intentObj):
    """Handle the intent."""
    hass = intentObj.hass
    slots = intentObj.slots
    
    itemDesc = slots.get("item_description", {}).get("value", "")
    location = slots.get("location", {}).get("value", "")
    _LOGGER.debug(f"AddItem intent: {itemDesc} to {location}")
    
    client = hass.data[DOMAIN]["client"]
    query = f"add {itemDesc} to {location}"
    result = await client.queryLlm(query, "add_item")
    
    response = intentObj.create_response()
    spokenText = result.get("spoken", "I couldn't add that item")
    response.async_set_speech(spokenText)
    
    return response


class FindSpaceIntentHandler(intent.IntentHandler):
  """Handle FindSpace intent."""
  
  intent_type = "FindSpace"
  slot_schema = {
    "item_description": cv.string
  }
  
  async def async_handle(self, intentObj):
    """Handle the intent."""
    hass = intentObj.hass
    slots = intentObj.slots
    
    itemDesc = slots.get("item_description", {}).get("value", "")
    _LOGGER.debug(f"FindSpace intent triggered for: {itemDesc}")
    
    client = hass.data[DOMAIN]["client"]
    result = await client.queryLlm(f"find space for {itemDesc}", "find_space")
    
    response = intentObj.create_response()
    spokenText = result.get("spoken", "I couldn't find space")
    response.async_set_speech(spokenText)
    
    return response
