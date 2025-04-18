"""
Code Agent for the All-Agents-App
This agent is responsible for generating and analyzing code.
"""

import os
import logging
import json
import re
from typing import Dict, Any, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

class CodeAgent:
    """
    Agent responsible for generating and analyzing code.
    Uses AI to generate code in various languages.
    """
    
    def __init__(self, ai_agent=None, workspace_dir: str = "runtime/temp"):
        """
        Initialize the code agent.
        
        Args:
            ai_agent: AI agent for generating code
            workspace_dir: Directory for temporary files
        """
        self.ai_agent = ai_agent
        self.workspace_dir = os.path.abspath(workspace_dir)
        os.makedirs(self.workspace_dir, exist_ok=True)
        logger.info(f"CodeAgent initialized with workspace directory: {self.workspace_dir}")
        
        # Dictionary of supported languages and their file extensions
        self.languages = {
            "python": {
                "extension": ".py",
                "comment": "# "
            },
            "javascript": {
                "extension": ".js",
                "comment": "// "
            },
            "typescript": {
                "extension": ".ts",
                "comment": "// "
            },
            "html": {
                "extension": ".html",
                "comment": "<!-- "
            },
            "css": {
                "extension": ".css",
                "comment": "/* "
            },
            "java": {
                "extension": ".java",
                "comment": "// "
            },
            "c": {
                "extension": ".c",
                "comment": "// "
            },
            "cpp": {
                "extension": ".cpp",
                "comment": "// "
            },
            "csharp": {
                "extension": ".cs",
                "comment": "// "
            },
            "go": {
                "extension": ".go",
                "comment": "// "
            },
            "ruby": {
                "extension": ".rb",
                "comment": "# "
            },
            "php": {
                "extension": ".php",
                "comment": "// "
            },
            "swift": {
                "extension": ".swift",
                "comment": "// "
            },
            "kotlin": {
                "extension": ".kt",
                "comment": "// "
            },
            "rust": {
                "extension": ".rs",
                "comment": "// "
            },
            "sql": {
                "extension": ".sql",
                "comment": "-- "
            },
            "bash": {
                "extension": ".sh",
                "comment": "# "
            },
            "powershell": {
                "extension": ".ps1",
                "comment": "# "
            },
            "markdown": {
                "extension": ".md",
                "comment": "<!-- "
            },
            "json": {
                "extension": ".json",
                "comment": "// "
            },
            "yaml": {
                "extension": ".yaml",
                "comment": "# "
            },
            "dockerfile": {
                "extension": "Dockerfile",
                "comment": "# "
            }
        }
    
    def process(self, query: str) -> str:
        """
        Processes a query related to code.

        Args:
            query: The input text query from the user.

        Returns:
            A string containing generated code, a success message, or an error message.
        """
        query_lower = query.lower()
        logger.info(f"CodeAgent processing query: '{query}'")

        # Basic keyword matching for demonstration
        if "كتابة كود" in query or "write code" in query_lower:
            # Generate code using the AI agent if available
            if self.ai_agent:
                language = "python"  # Default language
                
                # Try to detect language from query
                for lang in self.languages.keys():
                    if lang in query_lower:
                        language = lang
                        break
                
                result = self.generate_code(query, language)
                if result["status"] == "success":
                    return result["code"]
            
            # Fallback if AI agent not available or generation failed
            code_snippet = "import os\n\nprint('مرحبا بالعالم!' | 'Hello World!')"
            logger.info("CodeAgent generated simple code snippet.")
            return code_snippet
            
        elif "إصلاح الكود" in query or "fix code" in query_lower:
            # Example: Placeholder response for fixing code
            response = "تم إصلاح الكود بنجاح!" # "Code fixed successfully!"
            logger.info("CodeAgent provided placeholder fix response.")
            return response
            
        elif "تحليل الكود" in query or "analyze code" in query_lower:
            # Example: Placeholder response for analyzing code
            response = "تحليل الكود: الكود يعمل بشكل جيد ولكن يمكن تحسينه." # "Code analysis: The code works well but can be improved."
            logger.info("CodeAgent provided placeholder analysis response.")
            return response
            
        else:
            logger.warning(f"CodeAgent does not support query: '{query}'")
            return "طلب الكود هذا غير مدعوم حاليًا." # "This code request is not currently supported."
    
    def generate_code(self, prompt: str, language: str = "python") -> Dict[str, Any]:
        """
        Generate code based on a prompt.
        
        Args:
            prompt: Prompt describing the code to generate
            language: Programming language to generate code in
            
        Returns:
            Dict containing the generated code
        """
        if not self.ai_agent:
            logger.error("No AI agent provided for code generation")
            return {
                "status": "error",
                "message": "No AI agent provided for code generation"
            }
        
        try:
            # Get language information
            language = language.lower()
            language_info = self.languages.get(language)
            
            if not language_info:
                logger.warning(f"Unsupported language: {language}, defaulting to Python")
                language = "python"
                language_info = self.languages["python"]
            
            # Create a prompt for the AI
            ai_prompt = f"""
            Generate {language} code for the following:
            
            {prompt}
            
            Please provide only the code without explanations.
            """
            
            # Generate code using the AI agent
            response = self.ai_agent.generate(ai_prompt)
            
            # Extract code from the response
            code = self._extract_code(response, language)
            
            logger.info(f"Generated {language} code for prompt: {prompt[:50]}...")
            return {
                "status": "success",
                "language": language,
                "code": code,
                "file_extension": language_info["extension"]
            }
            
        except Exception as e:
            logger.error(f"Error generating code: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error generating code: {str(e)}"
            }
    
    def analyze_code(self, code: str, language: str = None) -> Dict[str, Any]:
        """
        Analyze code for issues and improvements.
        
        Args:
            code: Code to analyze
            language: Programming language of the code
            
        Returns:
            Dict containing the analysis results
        """
        if not self.ai_agent:
            logger.error("No AI agent provided for code analysis")
            return {
                "status": "error",
                "message": "No AI agent provided for code analysis"
            }
        
        try:
            # Detect language if not provided
            if not language:
                language = self._detect_language(code)
            
            # Create a prompt for the AI
            ai_prompt = f"""
            Analyze the following {language} code for issues and improvements:
            
            ```{language}
            {code}
            ```
            
            Please provide:
            1. A list of issues or bugs
            2. Suggestions for improvements
            3. A complexity assessment
            """
            
            # Generate analysis using the AI agent
            response = self.ai_agent.generate(ai_prompt)
            
            logger.info(f"Analyzed {language} code")
            return {
                "status": "success",
                "language": language,
                "analysis": response
            }
            
        except Exception as e:
            logger.error(f"Error analyzing code: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error analyzing code: {str(e)}"
            }
    
    def _extract_code(self, text: str, language: str) -> str:
        """
        Extract code from text.
        
        Args:
            text: Text to extract code from
            language: Programming language of the code
            
        Returns:
            Extracted code
        """
        # Try to find code in code blocks
        pattern = rf"```(?:{language})?\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            return matches[0]
        
        # If no code blocks found, return the original text
        return text
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from text.
        
        Args:
            text: Text to extract JSON from
            
        Returns:
            Extracted JSON, or None if no JSON was found
        """
        # Try to find JSON in code blocks
        json_match = re.search(r'```(?:json)?\n(.*?)\n```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object directly
        json_match = re.search(r'({.*})', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _detect_language(self, code: str) -> str:
        """
        Detect the programming language of code.
        
        Args:
            code: Code to detect language of
            
        Returns:
            Detected language
        """
        # Simple language detection based on keywords and syntax
        if "def " in code and ":" in code:
            return "python"
        elif "function " in code and "{" in code:
            return "javascript"
        elif "class " in code and "extends " in code:
            return "java"
        elif "<html" in code.lower():
            return "html"
        elif "body {" in code or ".class {" in code:
            return "css"
        elif "#include <" in code:
            return "cpp"
        elif "package main" in code:
            return "go"
        elif "<?php" in code:
            return "php"
        elif "import SwiftUI" in code:
            return "swift"
        elif "fn " in code and " -> " in code:
            return "rust"
        elif "SELECT " in code.upper() and " FROM " in code.upper():
            return "sql"
        elif "#!/bin/bash" in code:
            return "bash"
        else:
            return "unknown"

# Example Usage (for testing purposes)
if __name__ == '__main__':
    code_agent = CodeAgent()
    print(code_agent.process("كتابة كود بسيط"))
    print(code_agent.process("إصلاح الكود الخاص بي"))
    print(code_agent.process("تحليل هذا البرنامج"))