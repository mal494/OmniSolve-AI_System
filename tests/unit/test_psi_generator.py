"""
Unit tests for Core.utils.psi_generator module.
Tests Project State Interface generation and caching.
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
from Core.utils.psi_generator import PSIGenerator


class TestPSIGenerator:
    """Tests for PSIGenerator class."""

    @pytest.fixture
    def temp_projects_dir(self):
        """Create a temporary projects directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def psi_gen(self, temp_projects_dir, monkeypatch):
        """Create a PSIGenerator with temporary projects directory."""
        # Patch the PROJECTS_DIR constant before importing
        import Core.config.constants as constants
        monkeypatch.setattr(constants, 'PROJECTS_DIR', temp_projects_dir)
        # Reload to apply the patch
        from Core.utils.psi_generator import PSIGenerator
        gen = PSIGenerator()
        return gen

    def test_psi_generator_initialization(self, psi_gen):
        """Test PSIGenerator initializes correctly."""
        assert psi_gen is not None
        assert hasattr(psi_gen, '_cache')
        # Check the cache attribute name (might be different)
        assert hasattr(psi_gen, '_projects_dir') or hasattr(psi_gen, 'projects_dir')

    def test_generate_psi_for_empty_project(self, psi_gen, temp_projects_dir):
        """Test PSI generation for non-existent project."""
        project_name = "test_empty_project"
        psi = psi_gen.generate_psi(project_name, use_cache=False)
        
        assert psi is not None
        assert "PROJECT STATE" in psi
        assert project_name in psi

    def test_generate_psi_with_simple_structure(self, psi_gen, temp_projects_dir):
        """Test PSI generation with simple file structure."""
        # Create a test project
        project_name = "test_simple"
        project_path = os.path.join(temp_projects_dir, project_name)
        os.makedirs(project_path)
        
        # Create some test files
        with open(os.path.join(project_path, "main.py"), "w") as f:
            f.write("print('Hello')")
        
        with open(os.path.join(project_path, "utils.py"), "w") as f:
            f.write("def helper():\n    pass")
        
        psi = psi_gen.generate_psi(project_name, use_cache=False)
        
        assert "main.py" in psi
        assert "utils.py" in psi
        assert project_name in psi

    def test_generate_psi_with_nested_structure(self, psi_gen, temp_projects_dir):
        """Test PSI generation with nested directory structure."""
        project_name = "test_nested"
        project_path = os.path.join(temp_projects_dir, project_name)
        
        # Create nested structure
        os.makedirs(os.path.join(project_path, "src", "lib"))
        
        with open(os.path.join(project_path, "main.py"), "w") as f:
            f.write("# Main file")
        
        with open(os.path.join(project_path, "src", "app.py"), "w") as f:
            f.write("# App file")
        
        with open(os.path.join(project_path, "src", "lib", "helper.py"), "w") as f:
            f.write("# Helper file")
        
        psi = psi_gen.generate_psi(project_name, use_cache=False)
        
        assert "main.py" in psi
        assert "src" in psi or "app.py" in psi
        assert "lib" in psi or "helper.py" in psi

    def test_psi_caching_works(self, psi_gen, temp_projects_dir):
        """Test that PSI caching reduces generation time."""
        project_name = "test_cache"
        project_path = os.path.join(temp_projects_dir, project_name)
        os.makedirs(project_path)
        
        with open(os.path.join(project_path, "test.py"), "w") as f:
            f.write("# Test file")
        
        # First call - no cache
        psi1 = psi_gen.generate_psi(project_name, use_cache=True)
        
        # Second call - should use cache
        psi2 = psi_gen.generate_psi(project_name, use_cache=True)
        
        # Both should be identical
        assert psi1 == psi2
        
        # Check cache was used
        cache_key = project_name
        assert cache_key in psi_gen._cache

    def test_psi_cache_invalidation(self, psi_gen, temp_projects_dir):
        """Test that cache can be invalidated."""
        project_name = "test_invalidate"
        project_path = os.path.join(temp_projects_dir, project_name)
        os.makedirs(project_path)
        
        with open(os.path.join(project_path, "test.py"), "w") as f:
            f.write("# Initial")
        
        # Generate with cache
        psi1 = psi_gen.generate_psi(project_name, use_cache=True)
        
        # Invalidate cache
        psi_gen.invalidate_cache(project_name)
        
        # Modify file
        with open(os.path.join(project_path, "test.py"), "a") as f:
            f.write("\n# Modified")
        
        # Generate again - should reflect changes
        psi2 = psi_gen.generate_psi(project_name, use_cache=False)
        
        # PSIs should differ since file changed
        assert psi1 != psi2

    def test_psi_filters_pycache(self, psi_gen, temp_projects_dir):
        """Test that __pycache__ directories are filtered out."""
        project_name = "test_filter"
        project_path = os.path.join(temp_projects_dir, project_name)
        os.makedirs(os.path.join(project_path, "__pycache__"))
        
        with open(os.path.join(project_path, "main.py"), "w") as f:
            f.write("# Main")
        
        with open(os.path.join(project_path, "__pycache__", "main.cpython-38.pyc"), "w") as f:
            f.write("binary")
        
        psi = psi_gen.generate_psi(project_name, use_cache=False)
        
        assert "main.py" in psi
        assert "__pycache__" not in psi

    def test_psi_filters_git(self, psi_gen, temp_projects_dir):
        """Test that .git directories are filtered out."""
        project_name = "test_git"
        project_path = os.path.join(temp_projects_dir, project_name)
        os.makedirs(os.path.join(project_path, ".git", "objects"))
        
        with open(os.path.join(project_path, "main.py"), "w") as f:
            f.write("# Main")
        
        psi = psi_gen.generate_psi(project_name, use_cache=False)
        
        assert "main.py" in psi
        assert ".git" not in psi

    def test_psi_filters_node_modules(self, psi_gen, temp_projects_dir):
        """Test that node_modules directories are filtered out."""
        project_name = "test_node"
        project_path = os.path.join(temp_projects_dir, project_name)
        os.makedirs(os.path.join(project_path, "node_modules", "package"))
        
        with open(os.path.join(project_path, "app.js"), "w") as f:
            f.write("// App")
        
        psi = psi_gen.generate_psi(project_name, use_cache=False)
        
        assert "app.js" in psi
        assert "node_modules" not in psi

    def test_get_cache_stats(self, psi_gen, temp_projects_dir):
        """Test cache statistics retrieval."""
        project_name = "test_stats"
        project_path = os.path.join(temp_projects_dir, project_name)
        os.makedirs(project_path)
        
        # Generate some cached PSIs
        psi_gen.generate_psi(project_name, use_cache=True)
        
        stats = psi_gen.get_cache_stats()
        
        assert isinstance(stats, dict)
        assert 'cached_projects' in stats
        assert 'cache_size' in stats
        assert project_name in stats['cached_projects']

    def test_psi_with_special_characters_in_filenames(self, psi_gen, temp_projects_dir):
        """Test PSI handles files with special characters."""
        project_name = "test_special"
        project_path = os.path.join(temp_projects_dir, project_name)
        os.makedirs(project_path)
        
        # Create files with special chars (that are valid on most systems)
        with open(os.path.join(project_path, "test-file.py"), "w") as f:
            f.write("# Dash")
        
        with open(os.path.join(project_path, "test_file.py"), "w") as f:
            f.write("# Underscore")
        
        psi = psi_gen.generate_psi(project_name, use_cache=False)
        
        assert "test-file.py" in psi or "test_file.py" in psi

    def test_psi_respects_use_cache_parameter(self, psi_gen, temp_projects_dir):
        """Test that use_cache parameter is respected."""
        project_name = "test_respect_cache"
        project_path = os.path.join(temp_projects_dir, project_name)
        os.makedirs(project_path)
        
        with open(os.path.join(project_path, "test.py"), "w") as f:
            f.write("# Original")
        
        # First call with cache disabled
        psi1 = psi_gen.generate_psi(project_name, use_cache=False)
        
        # Modify file
        with open(os.path.join(project_path, "test.py"), "w") as f:
            f.write("# Modified")
        
        # Call again with cache disabled - should see changes
        psi2 = psi_gen.generate_psi(project_name, use_cache=False)
        
        assert psi1 != psi2

    def test_psi_with_multiple_file_types(self, psi_gen, temp_projects_dir):
        """Test PSI includes various file types."""
        project_name = "test_types"
        project_path = os.path.join(temp_projects_dir, project_name)
        os.makedirs(project_path)
        
        # Create different file types
        files = {
            "script.py": "# Python",
            "data.json": '{"key": "value"}',
            "README.md": "# Readme",
            "config.txt": "config",
        }
        
        for filename, content in files.items():
            with open(os.path.join(project_path, filename), "w") as f:
                f.write(content)
        
        psi = psi_gen.generate_psi(project_name, use_cache=False)
        
        for filename in files.keys():
            assert filename in psi


class TestPSIGeneratorEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def psi_gen(self):
        """Create a PSIGenerator with default settings."""
        return PSIGenerator()

    def test_psi_with_empty_project_name(self, psi_gen):
        """Test PSI generation with empty project name."""
        psi = psi_gen.generate_psi("", use_cache=False)
        assert psi is not None
        # Should handle gracefully

    def test_psi_with_very_long_project_name(self, psi_gen):
        """Test PSI generation with very long project name."""
        long_name = "a" * 255  # Max filename length on most systems
        psi = psi_gen.generate_psi(long_name, use_cache=False)
        assert psi is not None

    def test_invalidate_nonexistent_cache(self, psi_gen):
        """Test invalidating cache for non-cached project."""
        # Should not raise error
        psi_gen.invalidate_cache("nonexistent_project")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
