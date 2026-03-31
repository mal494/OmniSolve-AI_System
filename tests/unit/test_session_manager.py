"""
Unit tests for Core.session.SessionManager.
Tests save/load round-trip, missing sessions, list, delete, and update.
"""
import json
import time
import tempfile
import shutil
from pathlib import Path

import pytest

from Core.session import SessionManager, SessionState


@pytest.fixture
def sessions_dir(tmp_path):
    """Temporary directory for session files."""
    d = tmp_path / "sessions"
    d.mkdir()
    return d


@pytest.fixture
def manager(sessions_dir):
    return SessionManager(sessions_dir)


class TestSessionManagerSaveLoad:
    """Round-trip tests for save() and load()."""

    def test_save_creates_json_file(self, manager, sessions_dir):
        state = SessionState(project_name="my_project", task="build a thing")
        path = manager.save(state)
        assert path.exists()
        assert path.suffix == ".json"

    def test_load_returns_none_for_missing_session(self, manager):
        result = manager.load("nonexistent_project")
        assert result is None

    def test_round_trip_preserves_fields(self, manager):
        state = SessionState(
            project_name="test_proj",
            task="create app",
            step="planner",
            psi="PSI text",
            file_list=[{"path": "main.py", "type": "python", "action": "create"}],
            blueprint="Some blueprint",
            files_written=["main.py"],
        )
        manager.save(state)
        loaded = manager.load("test_proj")

        assert loaded is not None
        assert loaded.project_name == "test_proj"
        assert loaded.task == "create app"
        assert loaded.step == "planner"
        assert loaded.psi == "PSI text"
        assert loaded.blueprint == "Some blueprint"
        assert loaded.files_written == ["main.py"]
        assert len(loaded.file_list) == 1

    def test_save_updates_timestamp(self, manager):
        state = SessionState(project_name="proj", task="task", timestamp=0.0)
        manager.save(state)
        loaded = manager.load("proj")
        assert loaded.timestamp > 0.0

    def test_load_returns_none_for_corrupted_file(self, manager, sessions_dir):
        # Write invalid JSON to the session file
        path = sessions_dir / "bad_proj.json"
        path.write_text("{ not valid json }", encoding="utf-8")
        result = manager.load("bad_proj")
        assert result is None


class TestSessionManagerUpdate:
    """Tests for the update() convenience method."""

    def test_update_creates_new_session(self, manager):
        state = manager.update("new_proj", "a task", step="psi", psi="psi text")
        assert state.project_name == "new_proj"
        assert state.psi == "psi text"
        assert state.step == "psi"

    def test_update_preserves_existing_fields(self, manager):
        # Save initial state
        manager.update("proj", "task", step="psi", psi="psi value")
        # Update to next step
        state = manager.update("proj", "task", step="architect",
                               file_list=[{"path": "main.py"}])
        # PSI should still be there
        assert state.psi == "psi value"
        assert state.step == "architect"
        assert len(state.file_list) == 1

    def test_update_persists_to_disk(self, manager, sessions_dir):
        manager.update("disk_proj", "task", step="planner", blueprint="bp")
        loaded = manager.load("disk_proj")
        assert loaded is not None
        assert loaded.blueprint == "bp"


class TestSessionManagerDelete:
    """Tests for delete()."""

    def test_delete_removes_file(self, manager):
        manager.update("del_proj", "task", step="psi")
        result = manager.delete("del_proj")
        assert result is True
        assert manager.load("del_proj") is None

    def test_delete_returns_false_for_missing(self, manager):
        result = manager.delete("does_not_exist")
        assert result is False


class TestSessionManagerList:
    """Tests for list_sessions()."""

    def test_empty_dir_returns_empty_list(self, manager):
        assert manager.list_sessions() == []

    def test_lists_all_sessions(self, manager):
        manager.update("proj_a", "task a", step="psi")
        time.sleep(0.01)
        manager.update("proj_b", "task b", step="architect")
        sessions = manager.list_sessions()
        assert len(sessions) == 2
        names = {s.project_name for s in sessions}
        assert "proj_a" in names
        assert "proj_b" in names

    def test_sorted_newest_first(self, manager):
        manager.update("old_proj", "task", step="psi")
        time.sleep(0.05)
        manager.update("new_proj", "task", step="psi")
        sessions = manager.list_sessions()
        assert sessions[0].project_name == "new_proj"
        assert sessions[1].project_name == "old_proj"


class TestSessionManagerPathSanitization:
    """Tests that project names are sanitized to prevent path traversal in filenames."""

    def test_sanitizes_traversal_chars(self, manager, sessions_dir):
        # The path sanitization should strip non-alphanumeric chars except -_
        state = SessionState(project_name="../evil", task="t")
        path = manager.save(state)
        # The resulting file should be inside sessions_dir (no escape)
        assert str(path).startswith(str(sessions_dir))
        assert ".." not in path.name
