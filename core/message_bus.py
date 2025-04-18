"""
Message Bus for the All-Agents-App
This module provides a message bus for communication between agents.
"""

import logging
import time
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageBus:
    """
    Message bus for communication between agents.
    Implements a publish-subscribe pattern.
    """
    
    def __init__(self):
        """
        Initialize the message bus.
        """
        # Dictionary to store subscribers
        self.subscribers = {}
        
        # Dictionary to store message history
        self.message_history = {}
        
        logger.info("MessageBus initialized")
    
    def subscribe(self, topic: str, callback: Callable[[Dict[str, Any]], None]) -> str:
        """
        Subscribe to a topic.
        
        Args:
            topic: Topic to subscribe to
            callback: Callback function to call when a message is published to the topic
            
        Returns:
            Subscription ID
        """
        subscription_id = str(uuid.uuid4())
        
        if topic not in self.subscribers:
            self.subscribers[topic] = {}
        
        self.subscribers[topic][subscription_id] = callback
        
        logger.info(f"Subscribed to topic '{topic}' with ID '{subscription_id}'")
        return subscription_id
    
    def unsubscribe(self, topic: str, subscription_id: str) -> bool:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
            subscription_id: Subscription ID
            
        Returns:
            True if unsubscribed successfully, False otherwise
        """
        if topic not in self.subscribers or subscription_id not in self.subscribers[topic]:
            logger.warning(f"Subscription '{subscription_id}' for topic '{topic}' not found")
            return False
        
        del self.subscribers[topic][subscription_id]
        
        # Remove the topic if there are no more subscribers
        if not self.subscribers[topic]:
            del self.subscribers[topic]
        
        logger.info(f"Unsubscribed from topic '{topic}' with ID '{subscription_id}'")
        return True
    
    def publish(self, topic: str, message: Dict[str, Any]) -> int:
        """
        Publish a message to a topic.
        
        Args:
            topic: Topic to publish to
            message: Message to publish
            
        Returns:
            Number of subscribers the message was delivered to
        """
        if topic not in self.subscribers:
            logger.info(f"No subscribers for topic '{topic}'")
            return 0
        
        # Add metadata to the message
        if "metadata" not in message:
            message["metadata"] = {}
        
        message["metadata"]["timestamp"] = time.time()
        message["metadata"]["topic"] = topic
        
        # Store the message in history
        if topic not in self.message_history:
            self.message_history[topic] = []
        
        self.message_history[topic].append(message)
        
        # Deliver the message to subscribers
        count = 0
        for callback in self.subscribers[topic].values():
            try:
                callback(message)
                count += 1
            except Exception as e:
                logger.error(f"Error delivering message to subscriber: {e}", exc_info=True)
        
        logger.info(f"Published message to topic '{topic}', delivered to {count} subscribers")
        return count
    
    async def publish_async(self, topic: str, message: Dict[str, Any]) -> int:
        """
        Publish a message to a topic asynchronously.
        
        Args:
            topic: Topic to publish to
            message: Message to publish
            
        Returns:
            Number of subscribers the message was delivered to
        """
        if topic not in self.subscribers:
            logger.info(f"No subscribers for topic '{topic}'")
            return 0
        
        # Add metadata to the message
        if "metadata" not in message:
            message["metadata"] = {}
        
        message["metadata"]["timestamp"] = time.time()
        message["metadata"]["topic"] = topic
        
        # Store the message in history
        if topic not in self.message_history:
            self.message_history[topic] = []
        
        self.message_history[topic].append(message)
        
        # Deliver the message to subscribers
        count = 0
        for callback in self.subscribers[topic].values():
            try:
                # Check if the callback is a coroutine function
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
                count += 1
            except Exception as e:
                logger.error(f"Error delivering message to subscriber: {e}", exc_info=True)
        
        logger.info(f"Published message to topic '{topic}', delivered to {count} subscribers")
        return count
    
    def get_message_history(self, topic: str) -> List[Dict[str, Any]]:
        """
        Get the message history for a topic.
        
        Args:
            topic: Topic to get history for
            
        Returns:
            List of messages
        """
        return self.message_history.get(topic, [])
    
    def clear_message_history(self, topic: str) -> bool:
        """
        Clear the message history for a topic.
        
        Args:
            topic: Topic to clear history for
            
        Returns:
            True if history was cleared, False if topic not found
        """
        if topic not in self.message_history:
            logger.warning(f"No message history for topic '{topic}'")
            return False
        
        self.message_history[topic] = []
        logger.info(f"Cleared message history for topic '{topic}'")
        return True
    
    def get_topics(self) -> List[str]:
        """
        Get a list of all topics.
        
        Returns:
            List of topics
        """
        return list(set(list(self.subscribers.keys()) + list(self.message_history.keys())))
    
    def get_subscriber_count(self, topic: str) -> int:
        """
        Get the number of subscribers for a topic.
        
        Args:
            topic: Topic to get subscriber count for
            
        Returns:
            Number of subscribers
        """
        if topic not in self.subscribers:
            return 0
        
        return len(self.subscribers[topic])