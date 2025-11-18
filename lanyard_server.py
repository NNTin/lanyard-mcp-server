#!/usr/bin/env python3
"""
Simple Lanyard MCP Server - Discord presence tracking via Lanyard API
"""
import os
import sys
import logging
from datetime import datetime, timezone
import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("lanyard-server")

# Initialize MCP server
mcp = FastMCP("lanyard")

# Configuration
LANYARD_API_BASE = "https://api.lanyard.rest/v1"
REQUEST_TIMEOUT = 10

# === UTILITY FUNCTIONS ===

def sanitize_user_id(user_id: str) -> str:
    """Sanitize and validate Discord user ID."""
    clean_id = user_id.strip()
    if not clean_id:
        raise ValueError("User ID cannot be empty")
    if not clean_id.isdigit():
        raise ValueError("User ID must contain only digits")
    if len(clean_id) < 17 or len(clean_id) > 20:
        raise ValueError("User ID must be between 17-20 digits")
    return clean_id

def format_timestamp(timestamp_ms: int) -> str:
    """Format millisecond timestamp to readable string."""
    try:
        dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return "Unknown"

def format_spotify_data(spotify: dict) -> str:
    """Format Spotify data into readable string."""
    if not spotify:
        return "Not listening to Spotify"
    
    song = spotify.get("song", "Unknown")
    artist = spotify.get("artist", "Unknown")
    album = spotify.get("album", "Unknown")
    
    output = f"🎵 Spotify Activity:\n"
    output += f"  Song: {song}\n"
    output += f"  Artist: {artist}\n"
    output += f"  Album: {album}\n"
    
    timestamps = spotify.get("timestamps", {})
    if timestamps.get("start"):
        output += f"  Started: {format_timestamp(timestamps['start'])}\n"
    if timestamps.get("end"):
        output += f"  Ends: {format_timestamp(timestamps['end'])}\n"
    
    return output

def format_activities(activities: list) -> str:
    """Format Discord activities into readable string."""
    if not activities:
        return "No activities"
    
    output = ""
    for i, activity in enumerate(activities, 1):
        name = activity.get("name", "Unknown")
        activity_type = activity.get("type", 0)
        
        type_names = {
            0: "Playing",
            1: "Streaming",
            2: "Listening to",
            3: "Watching",
            4: "Custom Status",
            5: "Competing in"
        }
        type_str = type_names.get(activity_type, "Activity")
        
        output += f"\n{i}. {type_str} {name}\n"
        
        if activity.get("details"):
            output += f"   Details: {activity['details']}\n"
        if activity.get("state"):
            output += f"   State: {activity['state']}\n"
    
    return output

def format_kv_data(kv: dict) -> str:
    """Format Lanyard KV data into readable string."""
    if not kv:
        return "No KV data"
    
    output = "📝 Custom KV Data:\n"
    for key, value in kv.items():
        output += f"  {key}: {value}\n"
    return output

# === MCP TOOLS ===

@mcp.tool()
async def get_user_presence(user_id: str = "") -> str:
    """Get Discord presence information for a user via Lanyard API - provide Discord user ID."""
    logger.info(f"Fetching presence for user ID: {user_id}")
    
    try:
        clean_id = sanitize_user_id(user_id)
    except ValueError as e:
        return f"❌ Invalid user ID: {str(e)}"
    
    url = f"{LANYARD_API_BASE}/users/{clean_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            result = response.json()
            
            if not result.get("success"):
                return f"❌ API returned unsuccessful response for user {clean_id}"
            
            data = result.get("data", {})
            
            # Extract user information
            discord_user = data.get("discord_user", {})
            username = discord_user.get("username", "Unknown")
            user_id_str = discord_user.get("id", clean_id)
            discriminator = discord_user.get("discriminator", "0")
            
            # Format user display
            if discriminator == "0":
                user_display = f"@{username}"
            else:
                user_display = f"{username}#{discriminator}"
            
            # Build output
            output = f"✅ Discord Presence for {user_display} ({user_id_str})\n\n"
            
            # Status
            status = data.get("discord_status", "unknown")
            status_emoji = {
                "online": "🟢",
                "idle": "🟡",
                "dnd": "🔴",
                "offline": "⚫"
            }
            output += f"Status: {status_emoji.get(status, '⚪')} {status.upper()}\n\n"
            
            # Platform info
            if data.get("active_on_discord_desktop"):
                output += "💻 Active on Desktop\n"
            if data.get("active_on_discord_mobile"):
                output += "📱 Active on Mobile\n"
            output += "\n"
            
            # Spotify
            spotify = data.get("spotify")
            if data.get("listening_to_spotify") and spotify:
                output += format_spotify_data(spotify)
                output += "\n"
            
            # Activities
            activities = data.get("activities", [])
            if activities:
                output += "🎮 Activities:"
                output += format_activities(activities)
                output += "\n"
            
            # KV data
            kv = data.get("kv", {})
            if kv:
                output += format_kv_data(kv)
            
            return output.strip()
            
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 404:
                return f"❌ User not found: {clean_id} (Discord user may not be using Lanyard)"
            elif status == 429:
                return "❌ Rate limit exceeded. Please try again later."
            else:
                return f"❌ API Error: HTTP {status}"
        except httpx.TimeoutException:
            return f"⏱️ Request timed out while fetching user {clean_id}"
        except Exception as e:
            logger.error(f"Error fetching presence: {e}")
            return f"❌ Error: {str(e)}"

@mcp.tool()
async def get_user_spotify(user_id: str = "") -> str:
    """Get Spotify listening information for a Discord user via Lanyard - provide Discord user ID."""
    logger.info(f"Fetching Spotify data for user ID: {user_id}")
    
    try:
        clean_id = sanitize_user_id(user_id)
    except ValueError as e:
        return f"❌ Invalid user ID: {str(e)}"
    
    url = f"{LANYARD_API_BASE}/users/{clean_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            result = response.json()
            
            if not result.get("success"):
                return f"❌ API returned unsuccessful response for user {clean_id}"
            
            data = result.get("data", {})
            discord_user = data.get("discord_user", {})
            username = discord_user.get("username", "Unknown")
            
            listening = data.get("listening_to_spotify", False)
            spotify = data.get("spotify")
            
            if not listening or not spotify:
                return f"🎵 {username} is not currently listening to Spotify"
            
            output = f"✅ Spotify Status for {username}\n\n"
            output += format_spotify_data(spotify)
            
            # Add album art URL
            album_art = spotify.get("album_art_url", "")
            if album_art:
                output += f"  Album Art: {album_art}\n"
            
            track_id = spotify.get("track_id", "")
            if track_id:
                output += f"  Track URL: https://open.spotify.com/track/{track_id}\n"
            
            return output.strip()
            
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 404:
                return f"❌ User not found: {clean_id}"
            elif status == 429:
                return "❌ Rate limit exceeded. Please try again later."
            else:
                return f"❌ API Error: HTTP {status}"
        except httpx.TimeoutException:
            return f"⏱️ Request timed out while fetching user {clean_id}"
        except Exception as e:
            logger.error(f"Error fetching Spotify data: {e}")
            return f"❌ Error: {str(e)}"

@mcp.tool()
async def get_user_kv(user_id: str = "") -> str:
    """Get Lanyard KV (key-value) custom data for a Discord user - provide Discord user ID."""
    logger.info(f"Fetching KV data for user ID: {user_id}")
    
    try:
        clean_id = sanitize_user_id(user_id)
    except ValueError as e:
        return f"❌ Invalid user ID: {str(e)}"
    
    url = f"{LANYARD_API_BASE}/users/{clean_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            result = response.json()
            
            if not result.get("success"):
                return f"❌ API returned unsuccessful response for user {clean_id}"
            
            data = result.get("data", {})
            discord_user = data.get("discord_user", {})
            username = discord_user.get("username", "Unknown")
            kv = data.get("kv", {})
            
            if not kv:
                return f"📝 {username} has no custom KV data set"
            
            output = f"✅ KV Data for {username}\n\n"
            output += format_kv_data(kv)
            
            return output.strip()
            
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 404:
                return f"❌ User not found: {clean_id}"
            elif status == 429:
                return "❌ Rate limit exceeded. Please try again later."
            else:
                return f"❌ API Error: HTTP {status}"
        except httpx.TimeoutException:
            return f"⏱️ Request timed out while fetching user {clean_id}"
        except Exception as e:
            logger.error(f"Error fetching KV data: {e}")
            return f"❌ Error: {str(e)}"

# === SERVER STARTUP ===
if __name__ == "__main__":
    logger.info("Starting Lanyard MCP server...")
    logger.info(f"API Base URL: {LANYARD_API_BASE}")
    
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)