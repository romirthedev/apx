"""
Overlay Interaction Manager
Enables AI to interact with the overlay interface and perform user actions programmatically.
"""

import asyncio
import json
import logging
import requests
from typing import Dict, Any, Optional, List
import base64
import os

logger = logging.getLogger(__name__)

class OverlayInteractionManager:
    """Manages AI interactions with the overlay interface."""
    
    def __init__(self, base_url: str = "http://localhost:8888"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Overlay-Interaction/1.0'
        })
    
    async def execute_command(self, command: str, context: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute a command through the overlay interface."""
        try:
            payload = {
                'command': command,
                'context': context or []
            }
            
            response = self.session.post(f"{self.base_url}/command", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Command executed: {command} -> {result.get('success', False)}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing command '{command}': {str(e)}")
            return {
                'success': False,
                'error': f"Command execution failed: {str(e)}"
            }
    
    async def take_screenshot(self) -> Dict[str, Any]:
        """Take a screenshot through the overlay interface."""
        try:
            response = self.session.post(f"{self.base_url}/capture_screenshot")
            response.raise_for_status()
            
            result = response.json()
            logger.info("Screenshot captured successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return {
                'success': False,
                'error': f"Screenshot failed: {str(e)}"
            }
    
    async def start_audio_capture(self) -> Dict[str, Any]:
        """Start continuous audio capture."""
        try:
            response = self.session.post(f"{self.base_url}/start_continuous_capture")
            response.raise_for_status()
            
            result = response.json()
            logger.info("Audio capture started")
            return result
            
        except Exception as e:
            logger.error(f"Error starting audio capture: {str(e)}")
            return {
                'success': False,
                'error': f"Audio capture start failed: {str(e)}"
            }
    
    async def stop_audio_capture(self) -> Dict[str, Any]:
        """Stop continuous audio capture."""
        try:
            response = self.session.post(f"{self.base_url}/stop_continuous_capture")
            response.raise_for_status()
            
            result = response.json()
            logger.info("Audio capture stopped")
            return result
            
        except Exception as e:
            logger.error(f"Error stopping audio capture: {str(e)}")
            return {
                'success': False,
                'error': f"Audio capture stop failed: {str(e)}"
            }
    
    async def get_system_capabilities(self) -> Dict[str, Any]:
        """Get available system capabilities."""
        try:
            response = self.session.get(f"{self.base_url}/capabilities")
            response.raise_for_status()
            
            result = response.json()
            logger.info("Retrieved system capabilities")
            return result
            
        except Exception as e:
            logger.error(f"Error getting capabilities: {str(e)}")
            return {
                'success': False,
                'error': f"Capabilities retrieval failed: {str(e)}"
            }
    
    async def analyze_meeting_context(self, transcript: str, conversation_summary: str = "", 
                                    trigger_reason: str = "ai_request") -> Dict[str, Any]:
        """Analyze meeting context and conversation."""
        try:
            payload = {
                'transcript': transcript,
                'conversation_summary': conversation_summary,
                'trigger_reason': trigger_reason,
                'timestamp': None  # Will be set by the server
            }
            
            response = self.session.post(f"{self.base_url}/analyze_meeting", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info("Meeting context analyzed")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing meeting context: {str(e)}")
            return {
                'success': False,
                'error': f"Meeting analysis failed: {str(e)}"
            }
    
    async def clear_context(self) -> Dict[str, Any]:
        """Clear the current context."""
        try:
            response = self.session.post(f"{self.base_url}/context/clear")
            response.raise_for_status()
            
            result = response.json()
            logger.info("Context cleared")
            return result
            
        except Exception as e:
            logger.error(f"Error clearing context: {str(e)}")
            return {
                'success': False,
                'error': f"Context clear failed: {str(e)}"
            }
    
    async def refresh_context(self) -> Dict[str, Any]:
        """Refresh the current context."""
        try:
            response = self.session.post(f"{self.base_url}/refresh_context")
            response.raise_for_status()
            
            result = response.json()
            logger.info("Context refreshed")
            return result
            
        except Exception as e:
            logger.error(f"Error refreshing context: {str(e)}")
            return {
                'success': False,
                'error': f"Context refresh failed: {str(e)}"
            }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get system health status."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            
            result = response.json()
            logger.info("Health status retrieved")
            return result
            
        except Exception as e:
            logger.error(f"Error getting health status: {str(e)}")
            return {
                'success': False,
                'error': f"Health check failed: {str(e)}"
            }
    
    async def perform_web_search(self, query: str) -> Dict[str, Any]:
        """Perform a web search through the command interface."""
        search_command = f"search web for {query}"
        return await self.execute_command(search_command)
    
    async def create_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Create a file through the command interface."""
        create_command = f"create file {filename} with content: {content}"
        return await self.execute_command(create_command)
    
    async def read_file(self, filename: str) -> Dict[str, Any]:
        """Read a file through the command interface."""
        read_command = f"read file {filename}"
        return await self.execute_command(read_command)
    
    async def list_files(self, directory: str = ".") -> Dict[str, Any]:
        """List files in a directory through the command interface."""
        list_command = f"list files in {directory}"
        return await self.execute_command(list_command)
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information through the command interface."""
        info_command = "get system info"
        return await self.execute_command(info_command)
    
    async def open_application(self, app_name: str) -> Dict[str, Any]:
        """Open an application through the command interface."""
        open_command = f"open {app_name}"
        return await self.execute_command(open_command)
    
    def close(self):
        """Close the session."""
        if self.session:
            self.session.close()