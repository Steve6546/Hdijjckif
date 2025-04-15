# BrainOS - Multi-Agent AI Orchestration System

BrainOS is a comprehensive multi-agent AI orchestration system that coordinates 20 specialized AI models through OpenRouter.ai. It functions as an "artificial brain" where multiple agents collaborate autonomously to process tasks and solve complex problems.

## Key Features

- **20 Specialized AI Agents** - Each agent has unique capabilities and expertise
- **Autonomous Collaboration** - Agents work together without requiring user confirmation at each step
- **Multi-modal Processing** - Handles both text and image inputs
- **Dynamic Agent Selection** - Automatically chooses the most appropriate agents for each task
- **Performance Analytics** - Tracks and analyzes agent performance metrics

## System Architecture

BrainOS consists of the following main components:

1. **API Client** - Interfaces with OpenRouter.ai to access 20 different AI models
2. **Agent Module** - Defines the specialized agents and their capabilities
3. **Orchestrator** - Coordinates communication between agents and processes requests
4. **UI Layer** - Streamlit-based user interface for interaction with the system
5. **Utilities** - Helper functions for encoding, logging, and error handling

## Getting Started

### Prerequisites

- Python 3.9+
- OpenRouter API key

### Installation

1. Clone the repository
2. Install dependencies:
```
pip install -r requirements.txt
```
3. Create a `.env` file with your OpenRouter API key:
```
OPENROUTER_API_KEY=your_api_key_here
```

### Running the Application

Start the Streamlit application:

```
streamlit run app.py
```

The application will be available at http://localhost:5000

## Agent Categories

The 20 specialized AI agents are organized into the following categories:

- **Perception** - Visual analysis and pattern recognition
- **Analysis** - Reasoning, evaluation, and deep thinking
- **Creation** - Design, generation, and creative output
- **Validation** - Testing, security, and review
- **Coordination** - Integration, organization, and synthesis

## Usage

1. Enter text, upload an image, or both
2. Select which agents to include (or let the system auto-select)
3. Click "Process with AI Brain"
4. View individual agent responses and the integrated result

## Autonomous Processing

BrainOS functions as a true "artificial brain" by:

1. Intelligently selecting appropriate agents for each task
2. Processing information in parallel across multiple specialized agents
3. Autonomously coordinating communication between agents
4. Synthesizing multiple perspectives into integrated responses
5. Operating with full autonomy without requiring user confirmation at intermediate steps

## License

This project is licensed under the MIT License - see the LICENSE file for details.