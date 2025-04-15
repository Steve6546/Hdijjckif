"""
Database module for BrainOS - handles interaction with PostgreSQL database.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, 
    DateTime, Boolean, Float, ForeignKey, JSON, Table,
    MetaData, inspect
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# Set up logging
logger = logging.getLogger("brain_db")
logger.setLevel(logging.INFO)

# Get database connection string from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define database models
class Interaction(Base):
    """Model for storing user interactions with the system."""
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    input_text = Column(Text, nullable=True)
    image_provided = Column(Boolean, default=False)
    agent_count = Column(Integer)
    processing_time = Column(Float)
    responses = relationship("AgentResponse", back_populates="interaction", cascade="all, delete-orphan")
    integrated_response = Column(Text)
    
    def __repr__(self):
        return f"<Interaction(session_id='{self.session_id}', timestamp='{self.timestamp}')>"


class AgentResponse(Base):
    """Model for storing individual agent responses."""
    __tablename__ = "agent_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id", ondelete="CASCADE"), nullable=False)
    agent_name = Column(String, nullable=False)
    agent_model = Column(String, nullable=False)
    response_text = Column(Text, nullable=False)
    response_length = Column(Integer)
    processing_time = Column(Float, nullable=True)
    metrics = Column(JSON, nullable=True)
    
    interaction = relationship("Interaction", back_populates="responses")
    
    def __repr__(self):
        return f"<AgentResponse(agent_name='{self.agent_name}', interaction_id={self.interaction_id})>"


class AgentMetrics(Base):
    """Model for storing aggregated agent performance metrics."""
    __tablename__ = "agent_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, index=True, nullable=False)
    total_interactions = Column(Integer, default=0)
    avg_response_length = Column(Float, default=0)
    avg_processing_time = Column(Float, default=0)
    success_rate = Column(Float, default=100.0)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AgentMetrics(agent_name='{self.agent_name}', total_interactions={self.total_interactions})>"


# Create database tables
def init_db():
    """Initialize the database by creating all tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


# Database operation functions
def get_db_session():
    """Get a database session."""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        logger.error(f"Error getting database session: {e}")
        raise


def store_interaction(
    session_id: str,
    input_text: Optional[str],
    agent_responses: Dict[str, str],
    integrated_response: str,
    image_provided: bool = False,
    processing_time: float = 0.0,
    agent_models: Optional[Dict[str, str]] = None
) -> int:
    """
    Store an interaction and its agent responses in the database.
    
    Args:
        session_id: Unique identifier for the session
        input_text: The user's input text
        agent_responses: Dictionary of agent name to response text
        integrated_response: The final integrated response
        image_provided: Whether an image was included in the input
        processing_time: Total processing time in seconds
        agent_models: Dictionary mapping agent names to their model names
        
    Returns:
        int: The ID of the created interaction record
    """
    db = get_db_session()
    try:
        # Create interaction record
        interaction = Interaction(
            session_id=session_id,
            input_text=input_text or "",
            image_provided=image_provided,
            agent_count=len(agent_responses),
            processing_time=processing_time,
            integrated_response=integrated_response
        )
        db.add(interaction)
        db.flush()  # Get the ID without committing
        
        # Add individual agent responses
        for agent_name, response_text in agent_responses.items():
            agent_model = "unknown"
            if agent_models and agent_name in agent_models:
                agent_model = agent_models[agent_name]
                
            agent_response = AgentResponse(
                interaction_id=interaction.id,
                agent_name=agent_name,
                agent_model=agent_model,
                response_text=response_text,
                response_length=len(response_text)
            )
            db.add(agent_response)
            
            # Update agent metrics
            update_agent_metrics(db, agent_name, len(response_text))
        
        db.commit()
        logger.info(f"Stored interaction {interaction.id} with {len(agent_responses)} agent responses")
        return interaction.id
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error storing interaction: {e}")
        raise
    finally:
        db.close()


def update_agent_metrics(db: Session, agent_name: str, response_length: int):
    """
    Update the metrics for an agent.
    
    Args:
        db: Database session
        agent_name: Name of the agent
        response_length: Length of the agent's response
    """
    try:
        # Get or create metrics record
        metrics = db.query(AgentMetrics).filter(AgentMetrics.agent_name == agent_name).first()
        
        if not metrics:
            metrics = AgentMetrics(
                agent_name=agent_name,
                total_interactions=1,
                avg_response_length=response_length,
                last_updated=datetime.utcnow()
            )
            db.add(metrics)
        else:
            # Update the metrics with the new data
            new_total = metrics.total_interactions + 1
            metrics.avg_response_length = ((metrics.avg_response_length * metrics.total_interactions) + 
                                          response_length) / new_total
            metrics.total_interactions = new_total
            metrics.last_updated = datetime.utcnow()
    
    except Exception as e:
        logger.error(f"Error updating agent metrics: {e}")
        # Don't raise, as this is a non-critical operation


def get_agent_metrics(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get aggregated metrics for all agents.
    
    Args:
        limit: Maximum number of agents to return
        
    Returns:
        List of dictionaries with agent metrics
    """
    db = get_db_session()
    try:
        metrics = db.query(AgentMetrics).order_by(AgentMetrics.total_interactions.desc()).limit(limit).all()
        
        return [
            {
                "agent_name": m.agent_name,
                "total_interactions": m.total_interactions,
                "avg_response_length": m.avg_response_length,
                "avg_processing_time": m.avg_processing_time,
                "success_rate": m.success_rate,
                "last_updated": m.last_updated.isoformat()
            }
            for m in metrics
        ]
    
    except Exception as e:
        logger.error(f"Error getting agent metrics: {e}")
        return []
    finally:
        db.close()


def get_recent_interactions(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get most recent interactions.
    
    Args:
        limit: Maximum number of interactions to return
        
    Returns:
        List of dictionaries with interaction data
    """
    db = get_db_session()
    try:
        interactions = db.query(Interaction).order_by(Interaction.timestamp.desc()).limit(limit).all()
        
        return [
            {
                "id": i.id,
                "session_id": i.session_id,
                "timestamp": i.timestamp.isoformat(),
                "input_text": i.input_text[:100] + "..." if len(i.input_text) > 100 else i.input_text,
                "image_provided": i.image_provided,
                "agent_count": i.agent_count,
                "processing_time": i.processing_time
            }
            for i in interactions
        ]
    
    except Exception as e:
        logger.error(f"Error getting recent interactions: {e}")
        return []
    finally:
        db.close()


def get_interaction_details(interaction_id: int) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific interaction.
    
    Args:
        interaction_id: ID of the interaction to retrieve
        
    Returns:
        Dictionary with interaction details or None if not found
    """
    db = get_db_session()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        
        if not interaction:
            return None
            
        # Get agent responses for this interaction
        agent_responses = db.query(AgentResponse).filter(
            AgentResponse.interaction_id == interaction_id
        ).all()
        
        return {
            "id": interaction.id,
            "session_id": interaction.session_id,
            "timestamp": interaction.timestamp.isoformat(),
            "input_text": interaction.input_text,
            "image_provided": interaction.image_provided,
            "agent_count": interaction.agent_count,
            "processing_time": interaction.processing_time,
            "integrated_response": interaction.integrated_response,
            "agent_responses": [
                {
                    "agent_name": resp.agent_name,
                    "agent_model": resp.agent_model,
                    "response_text": resp.response_text,
                    "response_length": resp.response_length
                }
                for resp in agent_responses
            ]
        }
    
    except Exception as e:
        logger.error(f"Error getting interaction details: {e}")
        return None
    finally:
        db.close()


# Initialize the database tables when the module is imported
init_db()