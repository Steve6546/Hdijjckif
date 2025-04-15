from ai_agents import DesignAgent, ExecutionAgent, UpdateAgent, SecurityAgent

class AgentFactory:
    def create_agent(agent_type, master_agent=None):
        if agent_type == "design":
            return DesignAgent()
        elif agent_type == "execution":
            return ExecutionAgent()
        elif agent_type == "update":
            if not master_agent:
                raise ValueError("Master agent is required for UpdateAgent")
            return UpdateAgent(master_agent)
        elif agent_type == "security":
            if not master_agent:
                raise ValueError("Master agent is required for SecurityAgent")
            return SecurityAgent(master_agent)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

if __name__ == "__main__":
    # Example usage (for testing purposes)
    try:
        from ai_agents import MasterAgent
        master = MasterAgent()
        design_agent = AgentFactory.create_agent("design")
        update_agent = AgentFactory.create_agent("update", master)
        print("Agents created successfully.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")