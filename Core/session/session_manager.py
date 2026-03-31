"""
Session persistence for OmniSolve pipeline state.
Allows resuming a pipeline run from any completed step.
"""
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SessionState:
    """
    Captured state of an in-progress or completed OmniSolve pipeline run.

    Fields:
        project_name: Target project name
        task: Original task description
        timestamp: Unix timestamp of last update
        step: Last completed step name
               ('psi', 'architect', 'planner', 'developer', 'complete')
        psi: Project State Interface string (from Step 1)
        file_list: Architect output — list of file dicts (from Step 2)
        blueprint: Planner output — logic blueprint string (from Step 3)
        files_written: Paths of files successfully written so far (Step 4)
    """
    project_name: str
    task: str
    timestamp: float = field(default_factory=time.time)
    step: str = "init"
    psi: Optional[str] = None
    file_list: Optional[List[Dict[str, Any]]] = None
    blueprint: Optional[str] = None
    files_written: List[str] = field(default_factory=list)


class SessionManager:
    """
    Saves and loads pipeline session state to/from JSON files.

    Each project gets its own file: <sessions_dir>/<project_name>.json
    """

    def __init__(self, sessions_dir: Path):
        """
        Initialize the session manager.

        Args:
            sessions_dir: Directory where session JSON files are stored.
                          Created automatically if it does not exist.
        """
        self._dir = sessions_dir
        self._dir.mkdir(exist_ok=True, parents=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(self, state: SessionState) -> Path:
        """
        Persist *state* to disk.

        Args:
            state: The SessionState to save

        Returns:
            Path to the saved JSON file
        """
        state.timestamp = time.time()
        path = self._path_for(state.project_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(state), f, indent=2)
        return path

    def update(
        self,
        project_name: str,
        task: str,
        step: str,
        psi: Optional[str] = None,
        file_list: Optional[list] = None,
        blueprint: Optional[str] = None,
        files_written: Optional[List[str]] = None,
    ) -> SessionState:
        """
        Convenience method: load existing state (or create new), update fields, save.

        Returns the updated SessionState.
        """
        existing = self.load(project_name)
        if existing is None:
            state = SessionState(project_name=project_name, task=task)
        else:
            state = existing

        state.step = step
        if psi is not None:
            state.psi = psi
        if file_list is not None:
            state.file_list = file_list
        if blueprint is not None:
            state.blueprint = blueprint
        if files_written is not None:
            state.files_written = list(files_written)

        self.save(state)
        return state

    def load(self, project_name: str) -> Optional[SessionState]:
        """
        Load a saved session for *project_name*.

        Returns:
            SessionState if a session file exists, otherwise None
        """
        path = self._path_for(project_name)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return SessionState(**data)
        except (json.JSONDecodeError, TypeError, KeyError):
            # Corrupted file — treat as no session
            return None

    def delete(self, project_name: str) -> bool:
        """
        Remove the session file for *project_name*.

        Returns:
            True if the file existed and was deleted, False otherwise
        """
        path = self._path_for(project_name)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_sessions(self) -> List[SessionState]:
        """
        Return all saved sessions in this directory.

        Returns:
            List of SessionState objects (sorted newest first)
        """
        states = []
        for p in self._dir.glob("*.json"):
            project_name = p.stem
            state = self.load(project_name)
            if state is not None:
                states.append(state)
        return sorted(states, key=lambda s: s.timestamp, reverse=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _path_for(self, project_name: str) -> Path:
        # Sanitize project name to prevent directory traversal in filenames
        safe = "".join(c for c in project_name if c.isalnum() or c in "-_")
        return self._dir / f"{safe}.json"
