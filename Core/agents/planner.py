"""
Planner agent - Creates pseudocode/logic blueprints.
"""
from typing import Dict, Any, Optional

from ..brain import BrainAPI
from .base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    """
    Planner agent responsible for creating logic blueprints.
    Outputs pseudocode describing the implementation approach.
    """

    def __init__(self, brain: Optional[BrainAPI] = None):
        """Initialize the Planner agent."""
        super().__init__("Planner", brain=brain)

    def process(self, task: str, context: Dict[str, Any]) -> str:
        """
        Create logic blueprint for the given task.

        Args:
            task: The development request
            context: Dictionary containing 'psi', 'file_list', and optionally 'project_name'

        Returns:
            Pseudocode/logic blueprint as string
        """
        ctx = self.extract_context(context, ['psi', 'file_list', 'project_name'], {'psi': ''})
        psi = ctx['psi']
        file_list = ctx['file_list']
        project_name = ctx['project_name']

        self.logger.info(f"Creating logic blueprint for {len(file_list)} files")

        # Build examples for few-shot learning
        examples = """
Example Output:
FUNC main():
  INITIALIZE config
  CALL process_data(config)
  OUTPUT results
END FUNC

FUNC process_data(config):
  READ input_file
  TRANSFORM data
  RETURN transformed_data
END FUNC
"""

        # Build planner-specific prompt
        file_names = [f['path'] for f in file_list]
        plan_task = f"""Task: {task}

Files to implement: {', '.join(file_names)}

Create a LOGIC BLUEPRINT (Pseudocode) that describes:
1. What each file should do
2. Main functions/classes needed
3. How components interact
4. Data flow between modules

Write in clear pseudocode format. Focus on LOGIC, not implementation details.

LOGIC BLUEPRINT:"""

        prompt = self.build_prompt(plan_task, psi, examples)

        # Query the brain
        blueprint = self.query_brain(prompt, temperature=0.4)

        self.logger.info(f"Generated logic blueprint ({len(blueprint)} chars)")
        self.log_completion(
            'planner_complete',
            project_name=project_name,
            blueprint_length=len(blueprint),
            file_count=len(file_list)
        )

        return blueprint
