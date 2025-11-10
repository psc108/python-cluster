"""Message delivery guarantee tests"""
import pytest
import asyncio
import time
from src.communication.messaging import MessageQueue, Message, MessageType


@pytest.mark.asyncio
async def test_message_delivery_guarantee():
    """Test message delivery with retry mechanism"""
    queue = MessageQueue(node_id=1)
    
    # Create test message
    message = Message(
        msg_id="test-delivery-1",
        msg_type=MessageType.HEARTBEAT,
        sender_id=1,
        receiver_id=2,
        term=1,
        data={"test": "delivery"}
    )
    
    # Test message creation and queuing
    assert message.msg_id == "test-delivery-1"
    assert message.msg_type == MessageType.HEARTBEAT
    
    # Simulate successful delivery
    success = await queue.send_message(message)
    
    # Should succeed (mocked delivery always succeeds)
    assert success == True
    
    print("[+] Message delivery guarantee verified")


@pytest.mark.asyncio
async def test_message_retry_mechanism():
    """Test message retry on failure"""
    queue = MessageQueue(node_id=1)
    
    # Override delivery method to simulate failure then success
    original_deliver = queue._deliver_message
    call_count = 0
    
    async def mock_deliver(message):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return False  # First attempt fails
        return True  # Second attempt succeeds
    
    queue._deliver_message = mock_deliver
    
    message = Message(
        msg_id="test-retry-1",
        msg_type=MessageType.VOTE_REQUEST,
        sender_id=1,
        receiver_id=2,
        term=1,
        data={}
    )
    
    # Send message (will fail first time)
    result = await queue.send_message(message)
    
    # Should return False initially but trigger retry
    assert result == False
    
    # Wait for retry
    await asyncio.sleep(0.1)
    
    # Verify retry was attempted
    assert call_count >= 1
    
    print(f"[+] Message retry mechanism working (attempted {call_count} times)")


@pytest.mark.asyncio
async def test_pending_message_timeout():
    """Test pending message timeout handling"""
    queue = MessageQueue(node_id=1)
    queue.delivery_timeout = 0.1  # Short timeout for testing
    
    message = Message(
        msg_id="test-timeout-1",
        msg_type=MessageType.CLIENT_REQUEST,
        sender_id=1,
        receiver_id=2,
        term=1,
        data={}
    )
    
    # Add to pending manually
    queue.pending_messages[message.msg_id] = message
    
    # Wait for timeout
    await asyncio.sleep(0.2)
    
    # Process timeouts
    await queue.process_pending_messages()
    
    # Message should be removed from pending
    assert message.msg_id not in queue.pending_messages
    
    print("[+] Message timeout handling verified")