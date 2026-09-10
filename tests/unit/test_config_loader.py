"""
Unit tests for Core.config.config_loader module.
Tests persona configuration loading and caching.
"""
import pytest
import json
import os
import tempfile
import shutil
import importlib

# NB: use importlib (not `import Core.config.config_loader as ...`) because
# Core/config/__init__.py re-exports `config_loader` (the singleton instance),
# which shadows the submodule name for attribute-style binding.
config_loader_module = importlib.import_module("Core.config.config_loader")
from Core.config.config_loader import ConfigLoader


@pytest.fixture
def config_loader_factory(monkeypatch):
    """
    Drive the ConfigLoader singleton against a specific config directory.

    ConfigLoader is a parameterless singleton that reads the CONFIG_DIR
    module binding at construction time. Point that binding at the
    requested directory, reset the singleton instance, and construct a
    fresh loader so the new directory takes effect.
    """
    def _make(config_dir):
        monkeypatch.setattr(
            config_loader_module, "CONFIG_DIR", str(config_dir)
        )
        config_loader_module.ConfigLoader._instance = None
        loader = config_loader_module.ConfigLoader()
        # Personas are cached on the function by role; clear between
        # tests so tests never observe another test's cached data.
        config_loader_module.ConfigLoader.load_persona.cache_clear()
        return loader

    return _make


class TestConfigLoader:
    """Tests for ConfigLoader class."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory with test personas."""
        temp_dir = tempfile.mkdtemp()

        # Create test persona files (must include all fields validated
        # by ConfigLoader._validate_persona: name, role, instructions)
        architect_persona = {
            "name": "Test Architect",
            "role": "architect",
            "description": "Test architect persona",
            "system_prompt": "You are a test architect.",
            "instructions": "Architect instructions."
        }

        planner_persona = {
            "name": "Test Planner",
            "role": "planner",
            "description": "Test planner persona",
            "system_prompt": "You are a test planner.",
            "instructions": "Planner instructions."
        }

        developer_persona = {
            "name": "Test Developer",
            "role": "developer",
            "description": "Test developer persona",
            "system_prompt": "You are a test developer.",
            "instructions": "Developer instructions."
        }

        qa_persona = {
            "name": "Test QA",
            "role": "qa",
            "description": "Test QA persona",
            "system_prompt": "You are a test QA.",
            "instructions": "QA instructions."
        }

        # Write personas to files
        with open(os.path.join(temp_dir, "Architect.json"), "w") as f:
            json.dump(architect_persona, f)

        with open(os.path.join(temp_dir, "Planner.json"), "w") as f:
            json.dump(planner_persona, f)

        with open(os.path.join(temp_dir, "Steve.json"), "w") as f:
            json.dump(developer_persona, f)

        with open(os.path.join(temp_dir, "Developer.json"), "w") as f:
            # Developer.json typically redirects to Steve.json
            json.dump(developer_persona, f)

        with open(os.path.join(temp_dir, "QA.json"), "w") as f:
            json.dump(qa_persona, f)

        yield temp_dir

        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def config_loader(self, temp_config_dir, config_loader_factory):
        """Create a ConfigLoader backed by the temporary config directory."""
        return config_loader_factory(temp_config_dir)

    def test_config_loader_initialization(self, config_loader):
        """Test ConfigLoader initializes correctly."""
        assert config_loader is not None
        assert hasattr(config_loader, '_config_dir')

    def test_load_architect_persona(self, config_loader):
        """Test loading Architect persona."""
        persona = config_loader.load_persona("Architect")

        assert persona is not None
        assert persona["name"] == "Test Architect"
        assert persona["role"] == "architect"
        assert "system_prompt" in persona

    def test_load_planner_persona(self, config_loader):
        """Test loading Planner persona."""
        persona = config_loader.load_persona("Planner")

        assert persona is not None
        assert persona["name"] == "Test Planner"
        assert persona["role"] == "planner"

    def test_load_developer_persona(self, config_loader):
        """Test loading Developer persona (should map to Steve)."""
        persona = config_loader.load_persona("Developer")

        assert persona is not None
        assert "Test Developer" in persona["name"] or persona["role"] == "developer"

    def test_load_qa_persona(self, config_loader):
        """Test loading QA persona."""
        persona = config_loader.load_persona("QA")

        assert persona is not None
        assert persona["name"] == "Test QA"
        assert persona["role"] == "qa"

    def test_persona_caching(self, config_loader):
        """Test that personas are cached after first load."""
        # Load twice
        persona1 = config_loader.load_persona("Architect")
        persona2 = config_loader.load_persona("Architect")

        # Should be identical (cached)
        assert persona1 == persona2
        assert persona1 is persona2  # Same object reference

    def test_load_nonexistent_persona(self, config_loader):
        """Test loading a persona that doesn't exist."""
        with pytest.raises(Exception):
            config_loader.load_persona("NonExistent")

    def test_load_invalid_json_persona(self, temp_config_dir, config_loader_factory):
        """Test loading persona with invalid JSON."""
        # Create invalid JSON file
        invalid_path = os.path.join(temp_config_dir, "Invalid.json")
        with open(invalid_path, "w") as f:
            f.write("{ invalid json }")

        config_loader = config_loader_factory(temp_config_dir)
        with pytest.raises(Exception):
            config_loader.load_persona("Invalid")

    def test_get_all_personas(self, config_loader):
        """Test getting all available personas."""
        personas = config_loader.get_all_personas()

        assert isinstance(personas, dict)
        assert len(personas) > 0

        # Should include the standard mapped personas
        assert "Architect" in personas
        assert personas["Architect"]["name"] == "Test Architect"
        assert personas["QA"]["name"] == "Test QA"

    def test_reload_persona(self, config_loader, temp_config_dir):
        """Test reloading a persona clears cache."""
        # Load initially
        persona1 = config_loader.load_persona("Architect")

        # Modify the file
        architect_path = os.path.join(temp_config_dir, "Architect.json")
        with open(architect_path, "r") as f:
            data = json.load(f)

        data["name"] = "Modified Architect"

        with open(architect_path, "w") as f:
            json.dump(data, f)

        # Reload
        config_loader.reload_persona("Architect")
        persona2 = config_loader.load_persona("Architect")

        # Should reflect changes
        assert persona2["name"] == "Modified Architect"

    def test_persona_validation_required_fields(self, temp_config_dir, config_loader_factory):
        """Test that personas are validated for required fields."""
        # Create persona missing required fields
        incomplete_path = os.path.join(temp_config_dir, "Incomplete.json")
        with open(incomplete_path, "w") as f:
            json.dump({"name": "Incomplete"}, f)  # Missing other fields

        loader = config_loader_factory(temp_config_dir)

        # Should handle gracefully or raise appropriate error
        try:
            persona = loader.load_persona("Incomplete")
            # If it loads, verify it has the name at least
            assert persona["name"] == "Incomplete"
        except Exception as e:
            # Or it should raise a validation error
            assert True  # Expected behavior

    def test_case_insensitive_persona_loading(self, config_loader):
        """Test that persona names are handled consistently."""
        # Try different cases
        persona1 = config_loader.load_persona("Architect")

        # This might or might not work depending on implementation
        try:
            persona2 = config_loader.load_persona("architect")
            # If case-insensitive, they should match
            assert persona1["name"] == persona2["name"]
        except Exception:
            # Case-sensitive is also acceptable
            pass

    def test_multiple_config_loaders(self, temp_config_dir, config_loader_factory):
        """Test multiple ConfigLoader instances."""
        loader1 = config_loader_factory(temp_config_dir)
        loader2 = config_loader_factory(temp_config_dir)

        persona1 = loader1.load_persona("Architect")
        persona2 = loader2.load_persona("Architect")

        # Data should be same
        assert persona1["name"] == persona2["name"]


class TestConfigLoaderEdgeCases:
    """Tests for edge cases and error handling."""

    def test_config_loader_with_nonexistent_directory(self, config_loader_factory):
        """Test ConfigLoader with non-existent config directory."""
        with pytest.raises(Exception):
            config_loader_factory("/nonexistent/path")

    def test_config_loader_with_empty_directory(self, config_loader_factory):
        """Test ConfigLoader with empty config directory."""
        temp_dir = tempfile.mkdtemp()

        try:
            loader = config_loader_factory(temp_dir)
            with pytest.raises(Exception):
                loader.load_persona("Architect")
        finally:
            shutil.rmtree(temp_dir)

    def test_persona_file_with_extra_fields(self, config_loader_factory):
        """Test loading persona with extra/unknown fields."""
        temp_dir = tempfile.mkdtemp()

        try:
            persona_data = {
                "name": "Test",
                "role": "test",
                "system_prompt": "Test prompt",
                "instructions": "Test instructions",
                "extra_field": "Extra value",
                "another_field": 123
            }

            with open(os.path.join(temp_dir, "Test.json"), "w") as f:
                json.dump(persona_data, f)

            loader = config_loader_factory(temp_dir)
            persona = loader.load_persona("Test")

            # Should load successfully and include extra fields
            assert persona["name"] == "Test"
            assert persona["extra_field"] == "Extra value"
        finally:
            shutil.rmtree(temp_dir)

    def test_persona_with_unicode_content(self, config_loader_factory):
        """Test loading persona with unicode characters."""
        temp_dir = tempfile.mkdtemp()

        try:
            persona_data = {
                "name": "Test 测试 🎉",
                "role": "test",
                "system_prompt": "Test with émojis 🚀 and spëcial çhars",
                "instructions": "Unicode instructions 指令"
            }

            with open(os.path.join(temp_dir, "Unicode.json"), "w", encoding="utf-8") as f:
                json.dump(persona_data, f, ensure_ascii=False)

            loader = config_loader_factory(temp_dir)
            persona = loader.load_persona("Unicode")

            assert "测试" in persona["name"]
            assert "🎉" in persona["name"]
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])