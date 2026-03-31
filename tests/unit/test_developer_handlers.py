"""
Unit tests for Core.agents.handlers — strategy pattern for Developer agent.
Tests handler can_handle(), registry ordering, and extract_result().
"""
import json
import pytest

from Core.agents.handlers import (
    FileTypeRegistry,
    GenericHandler,
    JSONConfigHandler,
    JSONHandler,
    PythonHandler,
)
from Core.exceptions.errors import CodeGenerationError


class TestPythonHandler:
    """Tests for PythonHandler."""

    def setup_method(self):
        self.handler = PythonHandler()

    def test_can_handle_py_files(self):
        assert self.handler.can_handle("main.py") is True
        assert self.handler.can_handle("src/utils.py") is True
        assert self.handler.can_handle("test_foo.py") is True

    def test_cannot_handle_non_py_files(self):
        assert self.handler.can_handle("config.json") is False
        assert self.handler.can_handle("README.md") is False
        assert self.handler.can_handle("main.js") is False

    def test_build_task_contains_file_path(self):
        task, examples = self.handler.build_task("src/main.py", "blueprint text")
        assert "src/main.py" in task
        assert "blueprint text" in task
        assert "python" in examples.lower()

    def test_extract_result_from_code_block(self):
        response = '```python\ndef hello():\n    print("hi")\n```'
        result = self.handler.extract_result(response, "main.py")
        assert "def hello" in result
        assert "```" not in result

    def test_extract_result_raises_on_empty_response(self):
        with pytest.raises(CodeGenerationError):
            self.handler.extract_result("no code here at all", "main.py")


class TestJSONConfigHandler:
    """Tests for JSONConfigHandler (config.json)."""

    def setup_method(self):
        self.handler = JSONConfigHandler()

    def test_can_handle_config_json(self):
        assert self.handler.can_handle("config.json") is True
        assert self.handler.can_handle("myapp/config.json") is True
        assert self.handler.can_handle("CONFIG.JSON") is True

    def test_cannot_handle_other_json(self):
        assert self.handler.can_handle("settings.json") is False
        assert self.handler.can_handle("data.json") is False

    def test_build_task_mentions_required_keys(self):
        task, _ = self.handler.build_task("config.json", "blueprint")
        assert "name" in task
        assert "version" in task
        assert "settings" in task

    def test_extract_result_parses_valid_json(self):
        valid_json = '{"name": "test", "version": "1.0", "settings": {"a": 1}}'
        result = self.handler.extract_result(valid_json, "config.json")
        parsed = json.loads(result)
        assert parsed["name"] == "test"

    def test_extract_result_raises_on_invalid_json(self):
        with pytest.raises(CodeGenerationError):
            self.handler.extract_result("not json at all !!!", "config.json")


class TestJSONHandler:
    """Tests for generic JSONHandler."""

    def setup_method(self):
        self.handler = JSONHandler()

    def test_can_handle_json_files(self):
        assert self.handler.can_handle("data.json") is True
        assert self.handler.can_handle("settings.json") is True
        assert self.handler.can_handle("nested/foo.json") is True

    def test_extract_result_normalizes_json(self):
        response = '{"key": "value", "num": 42}'
        result = self.handler.extract_result(response, "data.json")
        parsed = json.loads(result)
        assert parsed["key"] == "value"
        assert parsed["num"] == 42

    def test_extract_result_raises_on_non_json(self):
        with pytest.raises(CodeGenerationError):
            self.handler.extract_result("plain text, no JSON here", "data.json")


class TestGenericHandler:
    """Tests for GenericHandler catch-all."""

    def setup_method(self):
        self.handler = GenericHandler()

    def test_can_handle_any_file(self):
        for path in ["README.md", "Makefile", "script.sh", "data.csv", "image.png"]:
            assert self.handler.can_handle(path) is True

    def test_extract_result_strips_code_block(self):
        response = "```\nsome raw content\n```"
        result = self.handler.extract_result(response, "file.txt")
        assert "some raw content" in result
        assert "```" not in result

    def test_extract_result_falls_back_to_stripped_response(self):
        response = "  raw content without fences  "
        result = self.handler.extract_result(response, "Makefile")
        assert result == "raw content without fences"


class TestFileTypeRegistry:
    """Tests for FileTypeRegistry — ordering and dispatch."""

    def setup_method(self):
        self.registry = FileTypeRegistry()

    def test_empty_registry_returns_generic_handler(self):
        handler = self.registry.get_handler("anything.xyz")
        assert isinstance(handler, GenericHandler)

    def test_registered_handler_is_used(self):
        self.registry.register(PythonHandler())
        handler = self.registry.get_handler("main.py")
        assert isinstance(handler, PythonHandler)

    def test_first_matching_handler_wins(self):
        """JSONConfigHandler registered before JSONHandler should win for config.json."""
        self.registry.register(JSONConfigHandler())
        self.registry.register(JSONHandler())
        handler = self.registry.get_handler("config.json")
        assert isinstance(handler, JSONConfigHandler)

    def test_second_handler_used_when_first_doesnt_match(self):
        self.registry.register(JSONConfigHandler())
        self.registry.register(JSONHandler())
        handler = self.registry.get_handler("settings.json")
        assert isinstance(handler, JSONHandler)

    def test_generic_fallback_when_no_match(self):
        self.registry.register(PythonHandler())
        handler = self.registry.get_handler("README.md")
        assert isinstance(handler, GenericHandler)

    def test_registering_generic_handler_is_ignored(self):
        """GenericHandler registered explicitly should not be duplicated."""
        initial_count = len(self.registry._handlers)
        self.registry.register(GenericHandler())
        assert len(self.registry._handlers) == initial_count

    def test_default_registry_has_correct_order(self):
        """Verify the developer agent's default registry priorities."""
        from Core.agents.developer import _build_default_registry
        registry = _build_default_registry()

        assert isinstance(registry.get_handler("config.json"), JSONConfigHandler)
        assert isinstance(registry.get_handler("settings.json"), JSONHandler)
        assert isinstance(registry.get_handler("main.py"), PythonHandler)
        assert isinstance(registry.get_handler("Makefile"), GenericHandler)
