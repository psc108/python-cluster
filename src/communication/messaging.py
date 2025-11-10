"""Reliable inter-node messaging system"""
import asyncio
import json
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    HEARTBEAT = "heartbeat"
    VOTE_REQUEST = "vote_request"
    VOTE_RESPONSE = "vote_response"
    APPEND_ENTRIES = "append_entries"
    CLIENT_REQUEST = "client_request"


@dataclass
class Message:
    msg_id: str
    msg_type: MessageType
    sender_id: int
    receiver_id: int
    term: int
    data: Dict
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class MessageQueue:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.pending_messages: Dict[str, Message] = {}
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.delivery_timeout = 5.0  # seconds
        
    def register_handler(self, msg_type: MessageType, handler: Callable):
        """Register message handler"""
        self.message_handlers[msg_type] = handler
        
    async def send_message(self, message: Message) -> bool:
        """Send message with delivery guarantee"""
        try:
            # Store for retry logic
            self.pending_messages[message.msg_id] = message
            
            # Attempt delivery
            success = await self._deliver_message(message)
            
            if success:
                # Remove from pending on successful delivery
                self.pending_messages.pop(message.msg_id, None)
                return True
            else:
                # Schedule retry
                asyncio.create_task(self._retry_message(message))
                return False
                
        except Exception:
            return False
            
    async def _deliver_message(self, message: Message) -> bool:
        """Attempt to deliver message"""
        # Simplified - would make actual network call
        await asyncio.sleep(0.1)  # Simulate network delay
        return True
        
    async def _retry_message(self, message: Message):
        """Retry message delivery"""
        retries = 3
        delay = 1.0
        
        for attempt in range(retries):
            await asyncio.sleep(delay)
            
            if await self._deliver_message(message):
                self.pending_messages.pop(message.msg_id, None)
                return
                
            delay *= 2  # Exponential backoff
            
        # Failed after all retries
        self.pending_messages.pop(message.msg_id, None)
        
    async def handle_message(self, message: Message):
        """Handle incoming message"""
        handler = self.message_handlers.get(message.msg_type)
        if handler:
            await handler(message)
            
    async def process_pending_messages(self):
        """Process pending messages for timeout"""
        current_time = time.time()
        expired_messages = []
        
        for msg_id, message in self.pending_messages.items():
            if current_time - message.timestamp > self.delivery_timeout:
                expired_messages.append(msg_id)
                
        for msg_id in expired_messages:
            self.pending_messages.pop(msg_id, None)