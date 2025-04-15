# backend/agents/nlp_agent.py
# (Assuming this structure, placing it in agents/ for organization)

class NLPAgent:
    """
    Agent responsible for understanding natural language queries
    and translating them into structured actions.
    """
    def process(self, query: str) -> dict:
        """
        Processes a natural language query.

        Args:
            query: The input text query from the user.

        Returns:
            A dictionary containing the identified action and any parameters.
            Example: {"action": "create_website", "theme": "modern"}
                     {"action": "edit_image", "command": "white_hair"}
                     {"action": "unknown"}
        """
        query_lower = query.lower() # Use lower case for case-insensitive matching

        if "إنشاء موقع" in query or "create website" in query_lower:
            # Basic theme detection (can be expanded)
            theme = "modern" # Default theme
            if "حديث" in query or "modern" in query_lower:
                theme = "modern"
            elif "كلاسيكي" in query or "classic" in query_lower:
                theme = "classic"
            # Add more theme keywords as needed
            return {"action": "create_website", "theme": theme}

        elif "تعديل الصورة" in query or "edit image" in query_lower:
            # Basic command extraction (can be expanded)
            command = "default_edit" # Default command
            if "white_hair" in query_lower or "شعر أبيض" in query: # Example command
                 command = "white_hair"
            # Add more command keywords as needed
            return {"action": "edit_image", "command": command}

        # Add more NLP rules here for other actions

        else:
            # If no specific action is recognized
            return {"action": "unknown"}

# Example Usage (for testing purposes)
if __name__ == '__main__':
    nlp_agent = NLPAgent()
    print(nlp_agent.process("إنشاء موقع حديث"))
    print(nlp_agent.process("تعديل الصورة white_hair"))
    print(nlp_agent.process("ما هو الطقس اليوم؟"))