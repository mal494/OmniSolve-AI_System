"""
Base agent class with common functionality.
All specialized agents inherit from this class.
"""
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from ..brain import BrainAPI, CircuitBreaker, create_brain
from ..config import (
    DEFAULT_MAX_CONTEXT_LENGTH,
    DEFAULT_MAX_LENGTH,
    DEFAULT_TEMPERATURE,
    RETRY_TEMPERATURE_INCREMENT,
    MAX_RETRIES,
    RETRY_DELAY,
    RETRY_DELAY_MAX,
    STOP_TOKENS,
    CIRCUIT_BREAKER_THRESHOLD,
    CIRCUIT_BREAKER_TIMEOUT,
)
from ..config.config_loader import config_loader
from ..exceptions.errors import (
    BrainConnectionError,
    BrainResponseError,
    CircuitOpenError,
    RetryExhaustedError,
)
from ..logging import get_logger, audit_log

logger = get_logger('agents')


class BaseAgent(ABC):
    """
    Base class for all OmniSolve agents.
    Provides common functionality for querying the brain and handling responses.
    """

    def __init__(self, role: str, brain: Optional[BrainAPI] = None):
        """
        Initialize the agent.

        Args:
            role: The agent's role name (used to load persona)
            brain: Optional BrainAPI instance (dependency injection).
                   Defaults to the configured backend via create_brain().
        """
        self.role = role
        self.persona = config_loader.load_persona(role)
        self.logger = get_logger(f'agent.{role.lower()}')

        # Brain backend (injectable for testing / multi-LLM)
        self._brain: BrainAPI = brain if brain is not None else create_brain()

        # Per-agent circuit breaker
        self._circuit_breaker = CircuitBreaker(
            threshold=CIRCUIT_BREAKER_THRESHOLD,
            timeout=CIRCUIT_BREAKER_TIMEOUT,
            name=f"{role}_brain",
        )

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

    def query_brain(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_length: Optional[int] = None,
        max_context: Optional[int] = None,
        stop_tokens: Optional[List[str]] = None,
    ) -> str:
        """
        Query the AI brain with retry logic, exponential backoff, and circuit breaker.

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (default from config)
            max_length: Maximum response length
            max_context: Maximum context length
            stop_tokens: Custom stop tokens

        Returns:
            The brain's response text

        Raises:
            CircuitOpenError: If the circuit breaker is open
            BrainConnectionError: If unable to connect
            BrainResponseError: If response is invalid
            RetryExhaustedError: If all retries fail
        """
        temperature = temperature if temperature is not None else DEFAULT_TEMPERATURE
        max_length = max_length or DEFAULT_MAX_LENGTH
        max_context = max_context or DEFAULT_MAX_CONTEXT_LENGTH
        stop_tokens = stop_tokens or STOP_TOKENS

        last_error: Exception = BrainConnectionError("Initial error placeholder")
        current_temperature = temperature

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self.logger.debug(f"Querying brain (attempt {attempt}/{MAX_RETRIES})")

                result = self._circuit_breaker.call(
                    self._brain.generate,
                    prompt=prompt,
                    temperature=current_temperature,
                    max_length=max_length,
                    max_context=max_context,
                    stop_tokens=stop_tokens,
                )

                if not result.text:
                    raise BrainResponseError("Brain returned empty response")

                # Audit log with token tracking
                audit_log(
                    'brain_query',
                    agent=self.role,
                    attempt=attempt,
                    prompt_length=len(prompt),
                    response_length=len(result.text),
                    temperature=current_temperature,
                    tokens_used=result.tokens_used,
                    model=result.model,
                )

                self.logger.debug(
                    f"Brain query successful ({len(result.text)} chars"
                    + (f", {result.tokens_used} tokens" if result.tokens_used else "")
                    + ")"
                )
                return result.text

            except CircuitOpenError:
                # Circuit is open — don't retry, propagate immediately
                self.logger.error(
                    f"Circuit breaker is OPEN for {self.role} — "
                    "backend is unavailable, aborting retries"
                )
                raise

            except (BrainConnectionError, BrainResponseError) as e:
                last_error = e
                self.logger.warning(f"Brain error on attempt {attempt}: {e}")

            except Exception as e:
                last_error = BrainConnectionError(
                    "Unexpected error during brain query",
                    {'attempt': attempt, 'error': str(e)},
                )
                self.logger.error(
                    f"Unexpected error on attempt {attempt}: {e}", exc_info=True
                )

            # Exponential backoff before next attempt
            if attempt < MAX_RETRIES:
                delay = min(RETRY_DELAY * (2 ** (attempt - 1)), RETRY_DELAY_MAX)
                self.logger.info(
                    f"Retrying in {delay:.1f}s (exponential backoff, attempt {attempt})..."
                )
                time.sleep(delay)
                current_temperature = min(
                    1.0, temperature + (RETRY_TEMPERATURE_INCREMENT * attempt)
                )

        self.logger.error(f"All {MAX_RETRIES} retry attempts exhausted")
        raise RetryExhaustedError('brain_query', MAX_RETRIES, last_error)

    def build_prompt(
        self,
        task: str,
        context: str,
        examples: Optional[str] = None,
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

    def extract_context(
        self,
        context: Dict[str, Any],
        keys: List[str],
        defaults: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Extract multiple keys from context dictionary with default values.

        Args:
            context: The context dictionary
            keys: List of keys to extract
            defaults: Optional dict of custom defaults for specific keys.
                     For keys not in defaults:
                     - 'file_list' and 'files' default to []
                     - All other keys default to 'unknown'

        Returns:
            Dictionary with extracted values
        """
        defaults = defaults or {}
        result = {}

        for key in keys:
            if key in defaults:
                default_value = defaults[key]
            elif key in ('file_list', 'files'):
                default_value = []
            else:
                default_value = 'unknown'

            result[key] = context.get(key, default_value)

        return result

    def log_completion(self, event_name: str, **kwargs: Any) -> None:
        """
        Log agent completion with audit trail.

        Args:
            event_name: The event name for audit log
            **kwargs: Additional key-value pairs to log
        """
        audit_log(event_name, **kwargs)

    def handle_extraction_error(
        self,
        response: str,
        error_message: str,
        error_class: type,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
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
        tasks: List[tuple],
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
            return [agents[0].process(tasks[0][0], tasks[0][1])]

        self.logger.info(f"Executing {len(agents)} agents in parallel")

        results: List[Any] = [None] * len(agents)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_index = {}
            for i, (agent, (task, context)) in enumerate(zip(agents, tasks)):
                future = executor.submit(agent.process, task, context)
                future_to_index[future] = i

            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                    self.logger.debug(f"Agent {index} completed successfully")
                except Exception as e:
                    self.logger.error(f"Agent {index} failed: {e}")
                    raise

        self.logger.info("All parallel agents completed")
        return results
