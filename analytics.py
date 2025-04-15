"""
Analytics module for BrainOS - provides visualization and analysis of agent performance.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

# Import database functions
from database import get_agent_metrics, get_recent_interactions, get_interaction_details

# Set up logging
logger = logging.getLogger("brain_analytics")
logger.setLevel(logging.INFO)

def render_analytics_page():
    """Render the analytics page in the Streamlit app."""
    st.title("🧠 BrainOS Analytics")
    
    # Top section with metrics cards
    st.subheader("AI Agent Performance")
    
    try:
        # Get agent metrics from database
        agent_metrics = get_agent_metrics()
        
        if not agent_metrics:
            st.info("No agent interaction data available yet. Try processing some requests first.")
            return
            
        # Create metrics display
        cols = st.columns(4)
        
        # Calculate overall stats
        total_interactions = sum(metric["total_interactions"] for metric in agent_metrics)
        avg_response_length = sum(metric["avg_response_length"] * metric["total_interactions"] 
                               for metric in agent_metrics) / total_interactions if total_interactions > 0 else 0
        
        with cols[0]:
            st.metric("Total Interactions", f"{total_interactions:,}")
            
        with cols[1]:
            st.metric("Active Agents", f"{len(agent_metrics):,}")
            
        with cols[2]:
            st.metric("Avg Response Length", f"{avg_response_length:.0f} chars")
            
        with cols[3]:
            # Get most recent interaction timestamp
            recent_interactions = get_recent_interactions(limit=1)
            if recent_interactions:
                last_activity = recent_interactions[0]["timestamp"]
                st.metric("Last Activity", datetime.fromisoformat(last_activity).strftime("%Y-%m-%d %H:%M"))
            else:
                st.metric("Last Activity", "None")
        
        # Agent performance comparison
        st.subheader("Agent Performance Comparison")
        
        # Convert to dataframe for easier visualization
        df_metrics = pd.DataFrame(agent_metrics)
        
        # Filter to top N agents by interaction count
        top_n = min(10, len(df_metrics))
        top_agents = df_metrics.nlargest(top_n, "total_interactions")
        
        # Create bar chart for interactions by agent
        st.bar_chart(top_agents.set_index("agent_name")["total_interactions"])
        
        # Recent interactions
        st.subheader("Recent Interactions")
        recent = get_recent_interactions(limit=10)
        
        if recent:
            # Convert to dataframe
            df_recent = pd.DataFrame(recent)
            df_recent["timestamp"] = pd.to_datetime(df_recent["timestamp"])
            df_recent["formatted_time"] = df_recent["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # Display as table
            st.dataframe(
                df_recent[["id", "formatted_time", "input_text", "agent_count", "processing_time"]],
                column_config={
                    "id": "ID",
                    "formatted_time": "Timestamp",
                    "input_text": "Input",
                    "agent_count": "Agents Used",
                    "processing_time": "Processing Time (s)"
                },
                hide_index=True
            )
            
            # Add details expander for selected interaction
            with st.expander("View Interaction Details", expanded=False):
                selected_id = st.selectbox(
                    "Select interaction ID to view details:",
                    options=df_recent["id"].tolist()
                )
                
                if selected_id:
                    details = get_interaction_details(selected_id)
                    if details:
                        st.json(details)
                    else:
                        st.warning(f"No details found for interaction ID {selected_id}")
        else:
            st.info("No recent interactions recorded yet.")
            
    except Exception as e:
        logger.error(f"Error rendering analytics: {e}")
        st.error(f"Error loading analytics data: {str(e)}")
        st.info("This might be because the database tables haven't been properly initialized. Try processing a request first.")
    
    # Database Statistics
    with st.expander("Database Statistics", expanded=False):
        try:
            # Execute direct queries to get table counts
            from sqlalchemy import text
            from database import engine
            
            # Count records in each table
            with engine.connect() as connection:
                interaction_count = connection.execute(text("SELECT COUNT(*) FROM interactions")).scalar()
                response_count = connection.execute(text("SELECT COUNT(*) FROM agent_responses")).scalar()
                metrics_count = connection.execute(text("SELECT COUNT(*) FROM agent_metrics")).scalar()
                
            # Display stats
            cols = st.columns(3)
            cols[0].metric("Interactions", f"{interaction_count:,}")
            cols[1].metric("Agent Responses", f"{response_count:,}")
            cols[2].metric("Agent Metrics", f"{metrics_count:,}")
            
        except Exception as e:
            st.error(f"Could not retrieve database statistics: {str(e)}")

if __name__ == "__main__":
    # For testing
    render_analytics_page()