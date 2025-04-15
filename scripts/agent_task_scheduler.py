"""
Agent Task Scheduler for BrainOS.
Implements a self-organizing task assignment and scheduling system for distributed agent processing.
"""

import os
import sys
import json
import asyncio
import time
import random
import heapq
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Callable, Union

# Add root directory to path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.neural_bridge import NeuralBridge
    NEURAL_BRIDGE_AVAILABLE = True
except ImportError:
    NEURAL_BRIDGE_AVAILABLE = False
    print("Warning: NeuralBridge not available. Some features will be limited.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("task_scheduler")

@dataclass(order=True)
class PrioritizedTask:
    """Task with priority for the priority queue."""
    priority: int
    created_at: datetime = field(compare=False)
    task_id: str = field(compare=False)
    task_data: Dict[str, Any] = field(compare=False)
    assigned_agents: List[str] = field(default_factory=list, compare=False)
    status: str = field(default="pending", compare=False)
    result: Optional[Any] = field(default=None, compare=False)

class AgentTaskScheduler:
    """
    Task scheduler for distributed agent processing.
    Handles task prioritization, agent assignment, and parallel execution.
    """
    
    def __init__(self):
        """Initialize the task scheduler."""
        self.task_queue: List[PrioritizedTask] = []  # Priority queue for tasks
        self.active_tasks: Dict[str, PrioritizedTask] = {}  # Tasks currently being processed
        self.completed_tasks: Dict[str, PrioritizedTask] = {}  # Completed tasks
        self.agent_capabilities: Dict[str, List[str]] = {}  # Agent name -> capabilities
        self.agent_availability: Dict[str, bool] = {}  # Agent name -> is available
        self.agent_performance: Dict[str, Dict[str, float]] = {}  # Agent performance metrics
        self.task_dependencies: Dict[str, List[str]] = {}  # Task ID -> dependent task IDs
        self.running = False
        
        # Task type definitions with required capabilities and priorities
        self.task_types = {
            "analysis": {
                "required_capabilities": ["analysis", "reasoning"],
                "default_priority": 3,
                "estimated_duration": 60  # seconds
            },
            "creation": {
                "required_capabilities": ["generation", "creativity"],
                "default_priority": 2,
                "estimated_duration": 120  # seconds
            },
            "research": {
                "required_capabilities": ["research", "information_retrieval"],
                "default_priority": 4,
                "estimated_duration": 180  # seconds
            },
            "planning": {
                "required_capabilities": ["planning", "strategy"],
                "default_priority": 1,
                "estimated_duration": 90  # seconds
            },
            "execution": {
                "required_capabilities": ["implementation", "execution"],
                "default_priority": 5,  # highest priority
                "estimated_duration": 30  # seconds
            }
        }
    
    def register_agent(self, agent_name: str, capabilities: List[str]):
        """
        Register an agent with the scheduler.
        
        Args:
            agent_name: Name of the agent
            capabilities: List of agent capabilities
        """
        self.agent_capabilities[agent_name] = capabilities
        self.agent_availability[agent_name] = True
        self.agent_performance[agent_name] = {
            "tasks_completed": 0,
            "avg_processing_time": 0.0,
            "success_rate": 1.0
        }
        logger.info(f"Registered agent: {agent_name} with capabilities: {capabilities}")
    
    def add_task(self, 
                task_data: Dict[str, Any], 
                priority: Optional[int] = None,
                task_type: Optional[str] = None,
                dependencies: Optional[List[str]] = None) -> str:
        """
        Add a task to the scheduler.
        
        Args:
            task_data: Task data dictionary
            priority: Task priority (1-5, 5 being highest)
            task_type: Type of task for capability matching
            dependencies: List of task IDs that must complete first
            
        Returns:
            Task ID
        """
        # Generate a task ID
        task_id = f"task_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Determine priority
        if priority is None and task_type and task_type in self.task_types:
            priority = self.task_types[task_type]["default_priority"]
        elif priority is None:
            priority = 3  # default medium priority
        
        # Ensure priority is in range
        priority = max(1, min(5, priority))
        
        # Add task type to data
        if task_type:
            task_data["task_type"] = task_type
        
        # Create task object
        task = PrioritizedTask(
            priority=priority,
            created_at=datetime.now(),
            task_id=task_id,
            task_data=task_data
        )
        
        # Record dependencies
        if dependencies:
            self.task_dependencies[task_id] = dependencies
            
            # Check if dependencies exist
            for dep_id in dependencies:
                if (dep_id not in self.active_tasks and 
                    dep_id not in self.completed_tasks):
                    logger.warning(f"Task {task_id} depends on non-existent task {dep_id}")
        
        # Add to queue
        heapq.heappush(self.task_queue, task)
        logger.info(f"Added task {task_id} with priority {priority}")
        
        return task_id
    
    async def process_tasks(self, max_parallel: int = 3):
        """
        Process tasks from the queue.
        
        Args:
            max_parallel: Maximum number of parallel tasks
        """
        self.running = True
        logger.info(f"Started task processing with max {max_parallel} parallel tasks")
        
        while self.running:
            await self._process_cycle(max_parallel)
            await asyncio.sleep(1)  # Check every second
    
    async def _process_cycle(self, max_parallel: int):
        """Process a single cycle of tasks."""
        # Check if we can process more tasks
        available_slots = max_parallel - len(self.active_tasks)
        
        if available_slots <= 0 or not self.task_queue:
            return
            
        # Get tasks that can be processed
        processable_tasks = []
        remaining_tasks = []
        
        # Find tasks that can be processed (no unmet dependencies)
        while self.task_queue and len(processable_tasks) < available_slots:
            task = heapq.heappop(self.task_queue)
            
            # Check dependencies
            if task.task_id in self.task_dependencies:
                deps = self.task_dependencies[task.task_id]
                unmet_deps = [d for d in deps if d not in self.completed_tasks]
                
                if unmet_deps:
                    # Put back in queue, dependencies not met
                    remaining_tasks.append(task)
                    continue
            
            processable_tasks.append(task)
        
        # Put remaining tasks back in queue
        for task in remaining_tasks:
            heapq.heappush(self.task_queue, task)
        
        # Process each task
        for task in processable_tasks:
            # Assign agents
            assigned_agents = self._assign_agents(task)
            
            if not assigned_agents:
                logger.warning(f"No suitable agents available for task {task.task_id}")
                heapq.heappush(self.task_queue, task)  # Put back in queue
                continue
            
            # Update task with assigned agents
            task.assigned_agents = assigned_agents
            task.status = "processing"
            self.active_tasks[task.task_id] = task
            
            # Mark agents as unavailable
            for agent in assigned_agents:
                self.agent_availability[agent] = False
            
            # Start task processing
            asyncio.create_task(self._execute_task(task))
            
            logger.info(f"Started processing task {task.task_id} with agents: {assigned_agents}")
    
    def _assign_agents(self, task: PrioritizedTask) -> List[str]:
        """
        Assign appropriate agents to a task based on capabilities.
        
        Args:
            task: The task to assign agents to
            
        Returns:
            List of agent names
        """
        # Get task type to determine required capabilities
        task_type = task.task_data.get("task_type")
        required_capabilities = []
        
        if task_type and task_type in self.task_types:
            required_capabilities = self.task_types[task_type]["required_capabilities"]
        
        # Get custom required capabilities from task data
        custom_capabilities = task.task_data.get("required_capabilities", [])
        required_capabilities.extend(custom_capabilities)
        
        if not required_capabilities:
            # No specific requirements, assign any available agent
            available_agents = [a for a, available in self.agent_availability.items() 
                               if available]
            if available_agents:
                return [random.choice(available_agents)]
            return []
        
        # Find agents with matching capabilities
        matching_agents = []
        
        for agent, capabilities in self.agent_capabilities.items():
            # Check if agent is available
            if not self.agent_availability.get(agent, False):
                continue
                
            # Check if agent has required capabilities
            matches = sum(1 for cap in required_capabilities if cap in capabilities)
            if matches > 0:
                matching_score = matches / len(required_capabilities)
                matching_agents.append((agent, matching_score))
        
        # Sort by matching score
        matching_agents.sort(key=lambda x: x[1], reverse=True)
        
        # Get top agents (up to 3)
        top_agents = [agent for agent, score in matching_agents[:3]]
        
        return top_agents
    
    async def _execute_task(self, task: PrioritizedTask):
        """
        Execute a task with the assigned agents.
        
        Args:
            task: The task to execute
        """
        start_time = time.time()
        
        try:
            # Process with NeuralBridge if available
            if NEURAL_BRIDGE_AVAILABLE and task.assigned_agents:
                result = await NeuralBridge.process_task(
                    task=task.task_data,
                    agents=task.assigned_agents
                )
                task.result = result
                
            else:
                # Mock execution if NeuralBridge not available
                # In a real implementation, this would execute the task with assigned agents
                await self._mock_execute_task(task)
                
            # Mark as completed
            task.status = "completed"
            processing_time = time.time() - start_time
            
            # Update task data
            task.task_data["processing_time"] = processing_time
            task.task_data["completed_at"] = datetime.now().isoformat()
            
            # Update agent performance metrics
            for agent in task.assigned_agents:
                self._update_agent_performance(agent, processing_time, success=True)
            
            # Move to completed tasks
            self.completed_tasks[task.task_id] = task
            
            logger.info(f"Completed task {task.task_id} in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {str(e)}")
            task.status = "failed"
            task.task_data["error"] = str(e)
            
            # Update agent performance metrics
            for agent in task.assigned_agents:
                self._update_agent_performance(agent, time.time() - start_time, success=False)
        
        finally:
            # Remove from active tasks
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
                
            # Mark agents as available again
            for agent in task.assigned_agents:
                self.agent_availability[agent] = True
    
    async def _mock_execute_task(self, task: PrioritizedTask):
        """Mock task execution for testing without NeuralBridge."""
        # Get estimated duration based on task type
        task_type = task.task_data.get("task_type", "analysis")
        duration = self.task_types.get(task_type, {}).get("estimated_duration", 60)
        
        # Add some randomness
        duration = duration * (0.5 + random.random())
        
        # Wait for the estimated duration
        await asyncio.sleep(min(5, duration / 10))  # Scale down for testing
        
        # Generate mock result
        task.result = {
            "task_id": task.task_id,
            "status": "completed",
            "output": f"Processed {task_type} task with {len(task.assigned_agents)} agents",
            "processing_time": duration
        }
    
    def _update_agent_performance(self, agent_name: str, processing_time: float, success: bool):
        """Update performance metrics for an agent."""
        if agent_name not in self.agent_performance:
            return
            
        metrics = self.agent_performance[agent_name]
        
        # Update tasks completed
        metrics["tasks_completed"] += 1
        
        # Update average processing time
        old_avg = metrics["avg_processing_time"]
        metrics["avg_processing_time"] = ((old_avg * (metrics["tasks_completed"] - 1)) 
                                         + processing_time) / metrics["tasks_completed"]
        
        # Update success rate
        old_rate = metrics["success_rate"]
        old_total = metrics["tasks_completed"] - 1
        metrics["success_rate"] = ((old_rate * old_total) + (1.0 if success else 0.0)) / metrics["tasks_completed"]
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "task_id": task_id,
                "status": task.status,
                "priority": task.priority,
                "created_at": task.created_at.isoformat(),
                "assigned_agents": task.assigned_agents,
                "task_data": task.task_data
            }
        elif task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return {
                "task_id": task_id,
                "status": task.status,
                "priority": task.priority,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.task_data.get("completed_at"),
                "processing_time": task.task_data.get("processing_time"),
                "assigned_agents": task.assigned_agents,
                "result": task.result
            }
        
        return None
    
    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get the status of all registered agents."""
        status = {}
        
        for agent, capabilities in self.agent_capabilities.items():
            status[agent] = {
                "capabilities": capabilities,
                "available": self.agent_availability.get(agent, False),
                "performance": self.agent_performance.get(agent, {}),
                "active_tasks": [
                    task_id for task_id, task in self.active_tasks.items()
                    if agent in task.assigned_agents
                ]
            }
        
        return status
    
    def stop(self):
        """Stop the task scheduler."""
        self.running = False
        logger.info("Task scheduler stopped")

# Test function
async def test_task_scheduler():
    """Test the task scheduler with sample tasks and agents."""
    scheduler = AgentTaskScheduler()
    
    # Register some test agents
    scheduler.register_agent("analyst_agent", ["analysis", "reasoning", "evaluation"])
    scheduler.register_agent("creative_agent", ["creativity", "generation", "design"])
    scheduler.register_agent("research_agent", ["research", "information_retrieval"])
    scheduler.register_agent("executor_agent", ["implementation", "execution"])
    
    # Add some tasks
    task1 = scheduler.add_task(
        {"description": "Analyze user requirements for new project"},
        task_type="analysis"
    )
    
    task2 = scheduler.add_task(
        {"description": "Design user interface mockups"},
        task_type="creation"
    )
    
    # Add a dependent task
    task3 = scheduler.add_task(
        {"description": "Implement UI components"},
        task_type="execution",
        dependencies=[task2]  # Depends on task2
    )
    
    # Start processing
    processor = asyncio.create_task(scheduler.process_tasks(max_parallel=2))
    
    # Monitor tasks
    for _ in range(10):
        print(f"\nTask Status Update (iteration {_+1}):")
        for task_id in [task1, task2, task3]:
            status = scheduler.get_task_status(task_id)
            if status:
                print(f"Task {task_id}: {status['status']}")
        
        # Print agent status
        print("\nAgent Status:")
        agent_status = scheduler.get_agent_status()
        for agent, status in agent_status.items():
            print(f"{agent}: Available={status['available']}, " 
                 f"Tasks={status['active_tasks']}")
        
        await asyncio.sleep(1)
    
    # Stop the scheduler
    scheduler.stop()
    await processor
    
    # Final status
    print("\nFinal Task Status:")
    for task_id in [task1, task2, task3]:
        status = scheduler.get_task_status(task_id)
        if status:
            print(f"Task {task_id}: {status['status']}")
            if status['status'] == 'completed':
                print(f"  Result: {status.get('result')}")

if __name__ == "__main__":
    asyncio.run(test_task_scheduler())