"""
Unit tests for Core.orchestrator.OmniSolveOrchestrator.
Tests input validation, run() with mocked agents, and interactive mode.
"""
import pytest
from unittest.mock import patch, MagicMock

from Core.brain import MockBrainAPI


# --- Helpers ---

_ARCHITECT_RESPONSE = '[{"path": "main.py", "type": "python", "action": "create"}]'
_PLANNER_RESPONSE = "1. Define main function\n2. Print Hello World"
_DEVELOPER_RESPONSE = (
    '```python\ndef main():\n    print("Hello")\n\n'
    'if __name__ == "__main__":\n    main()\n```'
)
_QA_RESPONSE = "PASSED: Code looks good."


def _patch_all_query_brain(orch, arch=None, plan=None, dev=None, qa=None):
    """Patch query_brain on each agent with a specific return value."""
    patches = [
        patch.object(orch.architect, 'query_brain', return_value=arch or _ARCHITECT_RESPONSE),
        patch.object(orch.planner, 'query_brain', return_value=plan or _PLANNER_RESPONSE),
        patch.object(orch.developer, 'query_brain', return_value=dev or _DEVELOPER_RESPONSE),
        patch.object(orch.qa, 'query_brain', return_value=qa or _QA_RESPONSE),
    ]
    return patches


class TestInputValidation:
    """Verify that orchestrator CLI entry validates inputs before running."""

    def test_empty_project_name_rejected(self):
        """main() should return 1 for empty project name."""
        with patch("sys.argv", ["omnisolve", "-p", "", "-t", "valid task"]):
            from Core.orchestrator import main
            result = main()
        assert result == 1

    def test_project_name_with_spaces_rejected(self):
        """Project name with spaces should be rejected."""
        with patch("sys.argv", ["omnisolve", "-p", "my project name", "-t", "valid task"]):
            from Core.orchestrator import main
            result = main()
        assert result == 1

    def test_empty_task_rejected(self):
        """main() should return 1 for empty task."""
        with patch("sys.argv", ["omnisolve", "-p", "valid_proj", "-t", ""]):
            from Core.orchestrator import main
            result = main()
        assert result == 1


class TestOrchestratorRunWithMock:
    """Run the orchestrator end-to-end using patched agent methods."""

    def test_run_returns_true_on_success(self, tmp_path):
        """Full pipeline run with mocked agent responses should succeed."""
        from Core.orchestrator import OmniSolveOrchestrator

        orch = OmniSolveOrchestrator()

        patches = _patch_all_query_brain(orch)
        with patches[0], patches[1], patches[2], patches[3]:
            with patch("Core.orchestrator.psi_generator") as mock_psi:
                mock_psi.generate_psi.return_value = "PSI text"
                with patch("Core.orchestrator.file_manager") as mock_fm:
                    mock_fm.write_file.return_value = tmp_path / "main.py"
                    result = orch.run("test_project", "create a hello world script")

        assert result is True

    def test_run_returns_false_on_qa_failure(self, tmp_path):
        """Run should return False when QA always rejects."""
        from Core.orchestrator import OmniSolveOrchestrator

        orch = OmniSolveOrchestrator()

        patches = _patch_all_query_brain(orch, qa="FAILED: Code has errors.")
        with patches[0], patches[1], patches[2], patches[3]:
            with patch("Core.orchestrator.psi_generator") as mock_psi:
                mock_psi.generate_psi.return_value = "PSI text"
                with patch("Core.orchestrator.file_manager"):
                    result = orch.run("fail_project", "create something")

        assert result is False

    def test_interactive_mode_abort_on_no(self, tmp_path):
        """Interactive mode: if user types 'n', pipeline should abort."""
        from Core.orchestrator import OmniSolveOrchestrator

        orch = OmniSolveOrchestrator()

        patches = _patch_all_query_brain(orch)
        with patches[0], patches[1], patches[2], patches[3]:
            with patch("Core.orchestrator.psi_generator") as mock_psi:
                mock_psi.generate_psi.return_value = "PSI text"
                with patch("builtins.input", return_value="n"):
                    result = orch.run(
                        "interactive_proj",
                        "build something",
                        interactive=True,
                    )

        assert result is False

    def test_interactive_mode_proceeds_on_yes(self, tmp_path):
        """Interactive mode: if user types 'y', pipeline should continue."""
        from Core.orchestrator import OmniSolveOrchestrator

        orch = OmniSolveOrchestrator()

        patches = _patch_all_query_brain(orch)
        with patches[0], patches[1], patches[2], patches[3]:
            with patch("Core.orchestrator.psi_generator") as mock_psi:
                mock_psi.generate_psi.return_value = "PSI text"
                with patch("Core.orchestrator.file_manager") as mock_fm:
                    mock_fm.write_file.return_value = tmp_path / "main.py"
                    with patch("builtins.input", return_value="y"):
                        result = orch.run(
                            "yes_proj",
                            "build something",
                            interactive=True,
                        )

        assert result is True


class TestOrchestratorSessionResumption:
    """Tests for session save/load during pipeline run."""

    def test_run_saves_session_after_psi(self, tmp_path):
        """Session should be updated after Step 1 (PSI)."""
        from Core.session import SessionManager
        from Core.orchestrator import OmniSolveOrchestrator

        session_manager = SessionManager(tmp_path / "sessions")
        orch = OmniSolveOrchestrator()

        patches = _patch_all_query_brain(orch)
        with patches[0], patches[1], patches[2], patches[3]:
            with patch("Core.orchestrator.psi_generator") as mock_psi:
                mock_psi.generate_psi.return_value = "PSI test content"
                with patch("Core.orchestrator.file_manager") as mock_fm:
                    mock_fm.write_file.return_value = tmp_path / "main.py"
                    orch.run(
                        "session_proj",
                        "build it",
                        session_manager=session_manager,
                    )

        state = session_manager.load("session_proj")
        assert state is not None
        assert state.psi == "PSI test content"

    def test_run_resumes_from_saved_psi(self, tmp_path):
        """When resume=True, PSI should be loaded from session not regenerated."""
        from Core.session import SessionManager
        from Core.orchestrator import OmniSolveOrchestrator

        session_manager = SessionManager(tmp_path / "sessions")

        # Pre-save a session with PSI
        session_manager.update("resume_proj", "build it", step="psi", psi="SAVED PSI")

        orch = OmniSolveOrchestrator()
        psi_calls = []

        patches = _patch_all_query_brain(orch)
        with patches[0], patches[1], patches[2], patches[3]:
            with patch("Core.orchestrator.psi_generator") as mock_psi:
                def track_psi(*args, **kwargs):
                    psi_calls.append(1)
                    return "FRESH PSI"
                mock_psi.generate_psi.side_effect = track_psi
                with patch("Core.orchestrator.file_manager") as mock_fm:
                    mock_fm.write_file.return_value = tmp_path / "main.py"
                    orch.run(
                        "resume_proj",
                        "build it",
                        resume=True,
                        session_manager=session_manager,
                    )

        # PSI generate should NOT have been called (loaded from session)
        assert psi_calls == []
