"""
OmniSolve Orchestrator - Refactored Version 3.0
Coordinates AI agents to generate software projects.
"""
import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from .agents import (
    ArchitectAgent,
    PlannerAgent,
    DeveloperAgent,
    QAAgent
)
from .config import MAX_RETRIES, PARALLEL_FILE_GENERATION
from .exceptions import (
    OmniSolveError,
    CodeGenerationError,
)
from .logging import get_logger, audit_log
from .output import file_manager
from .utils import psi_generator
from .utils.validation import validate_project_name, validate_task_description

logger = get_logger('orchestrator')


class OmniSolveOrchestrator:
    """
    Main orchestrator for the OmniSolve system.
    Coordinates agents to design and generate software projects.
    """

    def __init__(self, brain=None):
        """
        Initialize the orchestrator and all agents.

        Args:
            brain: Optional BrainAPI instance for dependency injection.
                   If None, uses the default backend from config.
        """
        logger.info("Initializing OmniSolve Orchestrator v3.0")

        # Initialize agents (pass brain for DI if provided)
        self.architect = ArchitectAgent(brain=brain)
        self.planner = PlannerAgent(brain=brain)
        self.developer = DeveloperAgent(brain=brain)
        self.qa = QAAgent(brain=brain)

        logger.info("All agents initialized successfully")

    def _prompt_approval(self, step_name: str, summary: str) -> bool:
        """
        Prompt the user to approve a pipeline step in interactive mode.

        Args:
            step_name: Name of the step (e.g. 'ARCHITECT')
            summary: Short description of what was produced

        Returns:
            True to proceed, False to abort
        """
        print(f"\n{'─' * 50}")
        print(f"[{step_name}] {summary}")
        print("─" * 50)
        try:
            resp = input("Proceed? [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        return resp != 'n'

    def run(
        self,
        project_name: str,
        task: str,
        interactive: bool = False,
        resume: bool = False,
        session_manager=None,
    ) -> bool:
        """
        Execute the full development workflow.

        Args:
            project_name: Name of the project to create/modify
            task: Development task description
            interactive: If True, prompt for approval after each step
            resume: If True, attempt to resume from a saved session
            session_manager: Optional SessionManager for state persistence

        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()

        logger.info("=" * 60)
        logger.info("OMNISOLVE v3.0 - REFACTORED ARCHITECTURE")
        logger.info("=" * 60)
        logger.info(f"Project: {project_name}")
        logger.info(f"Task: {task}")
        if interactive:
            logger.info("Mode: Interactive")
        logger.info("=" * 60)

        audit_log(
            'project_start',
            project_name=project_name,
            task=task,
            interactive=interactive,
            timestamp=time.time()
        )

        # Try to load existing session if resuming
        saved_psi: Optional[str] = None
        saved_file_list = None
        saved_blueprint: Optional[str] = None
        saved_files_written: list = []

        if resume and session_manager is not None:
            state = session_manager.load(project_name)
            if state is not None:
                logger.info(f"Resuming session from step: {state.step}")
                saved_psi = state.psi
                saved_file_list = state.file_list
                saved_blueprint = state.blueprint
                saved_files_written = list(state.files_written or [])

        try:
            # Step 1: Generate PSI (cached or resumed)
            if saved_psi and resume:
                logger.info("\n[STEP 1] Resuming PSI from saved session...")
                psi = saved_psi
            else:
                logger.info("\n[STEP 1] Generating Project State Interface...")
                psi = psi_generator.generate_psi(project_name, use_cache=True)
            logger.info(f"PSI generated ({len(psi)} chars)")

            if session_manager is not None:
                session_manager.update(project_name, task, step='psi', psi=psi)

            # Step 2: Architect designs file structure
            if saved_file_list and resume:
                logger.info("\n[STEP 2] Resuming file list from saved session...")
                file_list = saved_file_list
            else:
                logger.info("\n[STEP 2] ARCHITECT: Designing file structure...")
                file_list = self.architect.process(task, {
                    'psi': psi,
                    'project_name': project_name
                })

            logger.info(f"Architecture complete: {len(file_list)} files planned")
            for file_entry in file_list:
                logger.info(f"  - {file_entry['path']}")

            if interactive:
                summary = f"Architect planned {len(file_list)} file(s): " + \
                          ", ".join(e['path'] for e in file_list[:5])
                if not self._prompt_approval("ARCHITECT", summary):
                    logger.info("User aborted after Architect step")
                    return False

            if session_manager is not None:
                session_manager.update(project_name, task, step='architect',
                                       psi=psi, file_list=file_list)

            # Step 3: Planner creates logic blueprint
            if saved_blueprint and resume:
                logger.info("\n[STEP 3] Resuming blueprint from saved session...")
                blueprint = saved_blueprint
            else:
                logger.info("\n[STEP 3] PLANNER: Creating logic blueprint...")
                blueprint = self.planner.process(task, {
                    'psi': psi,
                    'file_list': file_list,
                    'project_name': project_name
                })

            logger.info(f"Blueprint complete ({len(blueprint)} chars)")

            if interactive:
                preview = blueprint[:200].replace('\n', ' ')
                if not self._prompt_approval("PLANNER", f"Blueprint preview: {preview}..."):
                    logger.info("User aborted after Planner step")
                    return False

            if session_manager is not None:
                session_manager.update(project_name, task, step='planner',
                                       psi=psi, file_list=file_list, blueprint=blueprint)

            # Step 4: Developer generates code for each file
            logger.info("\n[STEP 4] DEVELOPER (Steve): Generating code...")

            files_written = len(saved_files_written)
            files_failed = 0
            pending_files = [
                (i, fe) for i, fe in enumerate(file_list, 1)
                if fe['path'] not in saved_files_written
            ]

            if PARALLEL_FILE_GENERATION and not interactive:
                files_written, files_failed = self._generate_files_parallel(
                    project_name, task, psi, blueprint, pending_files,
                    session_manager, files_written
                )
            else:
                for i, file_entry in pending_files:
                    file_path = file_entry['path']
                    logger.info(f"\n  [{i}/{len(file_list)}] Working on: {file_path}")

                    if interactive:
                        if not self._prompt_approval(
                            "DEVELOPER",
                            f"About to generate: {file_path}"
                        ):
                            logger.info(f"User skipped file: {file_path}")
                            files_failed += 1
                            continue

                    success = self._generate_and_validate_file(
                        project_name, file_path, task, psi, blueprint
                    )

                    if success:
                        files_written += 1
                        if session_manager is not None:
                            saved_files_written.append(file_path)
                            session_manager.update(
                                project_name, task, step='developer',
                                psi=psi, file_list=file_list, blueprint=blueprint,
                                files_written=saved_files_written
                            )
                    else:
                        files_failed += 1

            # Summary
            elapsed_time = time.time() - start_time
            logger.info(f"\n{'=' * 60}")
            logger.info("PROJECT COMPLETE")
            logger.info(f"{'=' * 60}")
            logger.info(f"Files written: {files_written}/{len(file_list)}")
            logger.info(f"Files failed:  {files_failed}/{len(file_list)}")
            logger.info(f"Time elapsed:  {elapsed_time:.1f}s")
            logger.info(f"{'=' * 60}")

            audit_log(
                'project_complete',
                project_name=project_name,
                files_written=files_written,
                files_failed=files_failed,
                elapsed_time=elapsed_time,
                success=files_failed == 0
            )

            return files_failed == 0

        except OmniSolveError as e:
            logger.error(f"OmniSolve error: {e}")
            if e.details:
                logger.error(f"Details: {e.details}")

            audit_log(
                'project_failed',
                project_name=project_name,
                error=str(e),
                error_type=type(e).__name__
            )
            return False

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)

            audit_log(
                'project_failed',
                project_name=project_name,
                error=str(e),
                error_type='unexpected'
            )
            return False

    def _generate_files_parallel(
        self,
        project_name: str,
        task: str,
        psi: str,
        blueprint: str,
        pending_files: list,
        session_manager,
        initial_written: int
    ):
        """Generate files in parallel using a thread pool."""
        files_written = initial_written
        files_failed = 0
        results = {}

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_path = {
                executor.submit(
                    self._generate_and_validate_file,
                    project_name, fe['path'], task, psi, blueprint
                ): fe['path']
                for _, fe in pending_files
            }

            for future in as_completed(future_to_path):
                file_path = future_to_path[future]
                try:
                    success = future.result()
                    results[file_path] = success
                    if success:
                        files_written += 1
                    else:
                        files_failed += 1
                        logger.error(f"Parallel generation failed for: {file_path}")
                except Exception as exc:
                    logger.error(f"Parallel generation raised for {file_path}: {exc}")
                    files_failed += 1

        return files_written, files_failed

    def _generate_and_validate_file(
        self,
        project_name: str,
        file_path: str,
        task: str,
        psi: str,
        blueprint: str
    ) -> bool:
        """
        Generate code for a single file with retry logic and QA validation.

        Args:
            project_name: Name of the project
            file_path: Path to the file to generate
            task: Original task description
            psi: Project state interface
            blueprint: Logic blueprint from planner

        Returns:
            True if file was successfully generated and validated
        """
        context = {
            'psi': psi,
            'blueprint': blueprint,
            'file_path': file_path,
            'project_name': project_name
        }

        previous_code = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"    Attempt {attempt}/{MAX_RETRIES}...")

                # Generate code
                if attempt == 1:
                    code = self.developer.process(task, context)
                else:
                    # Regenerate with feedback
                    feedback = "Previous attempt failed validation. Generate better code."
                    code = self.developer.regenerate_with_feedback(
                        task,
                        context,
                        feedback,
                        previous_code
                    )

                previous_code = code

                # Quick syntax check first
                is_valid, syntax_error = self.qa.quick_validate(code, file_path)
                if not is_valid:
                    logger.warning(f"    Syntax error: {syntax_error}")
                    if attempt < MAX_RETRIES:
                        continue
                    else:
                        logger.error(f"    Max retries exhausted for {file_path}")
                        return False

                # Full QA review
                logger.info("    Submitting to QA for review...")
                passed, review = self.qa.process("Review code", {
                    'code': code,
                    'file_path': file_path,
                    'project_name': project_name
                })

                if passed:
                    logger.info("    [PASS] QA passed, writing file...")
                    written_path = file_manager.write_file(
                        project_name,
                        file_path,
                        code,
                        validate=True
                    )
                    logger.info(f"    [PASS] File saved: {written_path}")
                    return True
                else:
                    logger.warning(f"    [FAIL] QA rejected: {review[:100]}...")
                    if attempt < MAX_RETRIES:
                        logger.info("    Retrying...")
                    else:
                        logger.error(f"    Max retries exhausted for {file_path}")
                        return False

            except CodeGenerationError as e:
                logger.error(f"    Code generation failed: {e}")
                if attempt >= MAX_RETRIES:
                    return False

            except Exception as e:
                logger.error(f"    Unexpected error: {e}", exc_info=True)
                if attempt >= MAX_RETRIES:
                    return False

        return False


def main():
    """Main entry point for the orchestrator."""
    parser = argparse.ArgumentParser(
        description="OmniSolve 3.0 — AI-powered multi-agent code generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  omnisolve -p MyProject -t "Create a REST API with Flask"
  omnisolve -p MyProject -t "Add authentication" --interactive
  omnisolve -p MyProject -t "Add authentication" --resume
  omnisolve -p MyProject -t "Test run" --backend mock
        """
    )
    parser.add_argument("--project", "-p", metavar="NAME",
                        help="Project name (letters, numbers, underscores, hyphens)")
    parser.add_argument("--task", "-t", metavar="DESCRIPTION",
                        help="Development task description")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Prompt for approval after each pipeline step")
    parser.add_argument("--backend", "-b",
                        choices=["kobold", "openai", "anthropic", "mock"],
                        help="LLM backend to use (overrides OMNISOLVE_BRAIN_BACKEND)")
    parser.add_argument("--resume", "-r", action="store_true",
                        help="Resume from a previously saved session")
    parser.add_argument("--parallel", action="store_true",
                        help="Generate files in parallel (overrides OMNISOLVE_PARALLEL)")

    args = parser.parse_args()

    try:
        print("\n" + "=" * 60)
        print("OMNISOLVE 3.0 - REFACTORED ARCHITECTURE")
        print("=" * 60)

        # Get project name (arg or prompt)
        project_name = args.project
        if not project_name:
            project_name = input("\nProject Name: ").strip()

        # Validate project name
        name_result = validate_project_name(project_name)
        if not name_result:
            print(f"\nError: {name_result.get_summary()}")
            return 1
        for w in name_result.warnings:
            print(f"Warning: {w}")

        # Get task (arg or prompt)
        task = args.task
        if not task:
            task = input("Development Request: ").strip()

        # Validate task description
        task_result = validate_task_description(task)
        if not task_result:
            print(f"\nError: {task_result.get_summary()}")
            return 1
        for w in task_result.warnings:
            print(f"Warning: {w}")

        # Override parallel setting if flag provided
        if args.parallel:
            import Core.config.constants as _const
            _const.PARALLEL_FILE_GENERATION = True

        # Override brain backend if provided
        brain = None
        if args.backend:
            import os
            os.environ["OMNISOLVE_BRAIN_BACKEND"] = args.backend
            from .brain import create_brain
            brain = create_brain(args.backend)

        # Load session manager if resuming
        session_manager = None
        if args.resume:
            try:
                from .session import SessionManager
                from .config.constants import SESSIONS_DIR
                from pathlib import Path
                session_manager = SessionManager(Path(SESSIONS_DIR))
            except ImportError:
                logger.warning("Session module not available; ignoring --resume")

        # Create and run orchestrator
        orchestrator = OmniSolveOrchestrator(brain=brain)
        success = orchestrator.run(
            project_name,
            task,
            interactive=args.interactive,
            resume=args.resume,
            session_manager=session_manager,
        )

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nFatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
