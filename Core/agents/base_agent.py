"""
Base agent class with common functionality.
All specialized agents inherit from this class.
"""
import time
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..config import (
    API_URL,
    API_TIMEOUT,
    DEFAULT_MAX_CONTEXT_LENGTH,
    DEFAULT_MAX_LENGTH,
    DEFAULT_TEMPERATURE,
    RETRY_TEMPERATURE_INCREMENT,
    MAX_RETRIES,
    RETRY_DELAY,
    STOP_TOKENS
)
from ..config.config_loader import config_loader
from ..exceptions.errors import (
    BrainConnectionError,
    BrainResponseError,
    RetryExhaustedError
)
from ..logging import get_logger, audit_log

logger = get_logger('agents')


class BaseAgent(ABC):
    """
    Base class for all OmniSolve agents.
    Provides common functionality for querying the brain and handling responses.
    """

    def __init__(self, role: str):
        """
        Initialize the agent.

        Args:
            role: The agent's role name (used to load persona)
        """
        self.role = role
        self.persona = config_loader.load_persona(role)
        self.logger = get_logger(f'agent.{role.lower()}')
        self.logger.info(f"{self.persona['name']} agent initialized")

    @abstractmethod
    def process(self, task: str, context: Dict[str, Any]) -> Any:
        """
        Process a task with the given context.
        Must be implemented by subclasses.

        Args:
            task: The task description
            context: Additional context for the task

        Returns:
            Processing result (type varies by agent)
        """
        pass

    def query_brain(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_length: Optional[int] = None,
        max_context: Optional[int] = None,
        stop_tokens: Optional[List[str]] = None
    ) -> str:
        """
        Query the AI brain with retry logic and error handling.

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (default from config)
            max_length: Maximum response length
            max_context: Maximum context length
            stop_tokens: Custom stop tokens

        Returns:
            The brain's response text

        Raises:
            BrainConnectionError: If unable to connect
            BrainResponseError: If response is invalid
            RetryExhaustedError: If all retries fail
        """
        temperature = temperature or DEFAULT_TEMPERATURE
        max_length = max_length or DEFAULT_MAX_LENGTH
        max_context = max_context or DEFAULT_MAX_CONTEXT_LENGTH
        stop_tokens = stop_tokens or STOP_TOKENS

        payload = {
            "prompt": prompt,
            "max_context_length": max_context,
            "max_length": max_length,
            "temperature": temperature,
            "stop_sequence": stop_tokens
        }

        last_error: Exception = BrainConnectionError("Initial error placeholder")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self.logger.debug(f"Querying brain (attempt {attempt}/{MAX_RETRIES})")

                response = requests.post(
                    API_URL,
                    json=payload,
                    timeout=API_TIMEOUT
                )
                response.raise_for_status()

                result = response.json()

                if 'results' not in result or len(result['results']) == 0:
                    raise BrainResponseError(
                        "Invalid response format: missing results",
                        {'response': result}
                    )

                text = result['results'][0]['text'].strip()

                if not text:
                    raise BrainResponseError("Brain returned empty response")

                # Log successful query
                audit_log(
                    'brain_query',
                    agent=self.role,
                    attempt=attempt,
                    prompt_length=len(prompt),
                    response_length=len(text),
                    temperature=temperature
                )

                self.logger.debug(f"Brain query successful (response: {len(text)} chars)")
                return text

            except requests.exceptions.Timeout as e:
                last_error = BrainConnectionError(
                    f"Request timed out after {API_TIMEOUT}s",
                    {'attempt': attempt, 'error': str(e)}
                )
                self.logger.warning(f"Timeout on attempt {attempt}: {e}")

            except requests.exceptions.ConnectionError as e:
                last_error = BrainConnectionError(
                    "Unable to connect to brain API",
                    {'attempt': attempt, 'error': str(e), 'url': API_URL}
                )
                self.logger.warning(f"Connection error on attempt {attempt}: {e}")

            except requests.exceptions.HTTPError as e:
                last_error = BrainResponseError(
                    f"HTTP error: {e.response.status_code}",
                    {'attempt': attempt, 'error': str(e)}
                )
                self.logger.warning(f"HTTP error on attempt {attempt}: {e}")

            except (BrainResponseError, BrainConnectionError) as e:
                last_error = e
                self.logger.warning(f"Brain error on attempt {attempt}: {e}")

            except Exception as e:
                last_error = BrainConnectionError(
                    "Unexpected error during brain query",
                    {'attempt': attempt, 'error': str(e)}
                )
                self.logger.error(f"Unexpected error on attempt {attempt}: {e}", exc_info=True)

            # If not the last attempt, wait before retrying
            if attempt < MAX_RETRIES:
                self.logger.info(f"Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)

                # Increase temperature slightly on retry
                payload['temperature'] = min(1.0, temperature + (RETRY_TEMPERATURE_INCREMENT * attempt))

        # All retries exhausted
        self.logger.error(f"All {MAX_RETRIES} retry attempts exhausted")
        raise RetryExhaustedError('brain_query', MAX_RETRIES, last_error)

    def build_prompt(
        self,
        task: str,
        context: str,
        examples: Optional[str] = None
    ) -> str:
        """
        Build a formatted prompt for the brain.

        Args:
            task: The task description
            context: PSI or other context
            examples: Optional few-shot examples

        Returns:
            Formatted prompt string
        """
        prompt = f"""SYSTEM ROLE: {self.persona['role']}
INSTRUCTIONS: {self.persona['instructions']}"""

        if examples:
            prompt += f"\n\n{examples}"

        prompt += f"""

[PINNED PROJECT CONTEXT]
{context}

[CURRENT TASK]
{task}

RESPONSE:
"""
        return prompt

    def get_name(self) -> str:
        """Get the agent's display name."""
        return self.persona.get('name', self.role)

    def get_role(self) -> str:
        """Get the agent's role."""
        return self.role

    def extract_context(self, context: Dict[str, Any], keys: List[str], defaults: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract multiple keys from context dictionary with default values.

        Args:
            context: The context dictionary
            keys: List of keys to extract
            defaults: Optional dict of custom defaults (otherwise uses 'unknown' for strings, empty list for lists)

        Returns:
            Dictionary with extracted values
        """
        defaults = defaults or {}
        result = {}
        
        for key in keys:
            if key in defaults:
                default_value = defaults[key]
            elif key in ['file_list', 'files']:
                default_value = []
            else:
                default_value = 'unknown'
            
            result[key] = context.get(key, default_value)
        
        return result

    def log_completion(self, event_name: str, **kwargs):
        """
        Log agent completion with audit trail.

        Args:
            event_name: The event name for audit log
            **kwargs: Additional key-value pairs to log
        """
        audit_log(event_name, **kwargs)

    def handle_extraction_error(self, response: str, error_message: str, error_class: type, context: Optional[Dict[str, Any]] = None):
        """
        Log and raise an error when extraction fails.

        Args:
            response: The response that failed to extract
            error_message: The error message to log and raise
            error_class: The exception class to raise
            context: Optional additional context for the error

        Raises:
            The specified error_class with the message and context
        """
        self.logger.error(f"{error_message}. Response: {response[:200]}")
        error_context = {'response': response[:500]}
        if context:
            error_context.update(context)
        raise error_class(error_message, error_context)


class ParallelAgentExecutor:
    """Executes multiple agents in parallel when appropriate."""

    def __init__(self, max_workers: int = 3):
        """
        Initialize the parallel executor.

        Args:
            max_workers: Maximum number of parallel workers
        """
        self.max_workers = max_workers
        self.logger = get_logger('parallel_executor')

    def execute_parallel(
        self,
        agents: List[BaseAgent],
        tasks: List[tuple[str, Dict[str, Any]]]
    ) -> List[Any]:
        """
        Execute multiple agents in parallel.

        Args:
            agents: List of agent instances
            tasks: List of (task_description, context) tuples

        Returns:
            List of results in the same order as input

        Raises:
            Exception: If any agent fails
        """
        if len(agents) != len(tasks):
            raise ValueError("Number of agents must match number of tasks")

        if len(agents) == 1:
            # No need for parallelization
            return [agents[0].process(tasks[0][0], tasks[0][1])]

        self.logger.info(f"Executing {len(agents)} agents in parallel")

        results = [None] * len(agents)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_index = {}
            for i, (agent, (task, context)) in enumerate(zip(agents, tasks)):
                future = executor.submit(agent.process, task, context)
                future_to_index[future] = i

            # Collect results as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    results[index] = result
                    self.logger.debug(f"Agent {index} completed successfully")
                except Exception as e:
                    self.logger.error(f"Agent {index} failed: {e}")
                    raise

        self.logger.info("All parallel agents completed")
        return results
