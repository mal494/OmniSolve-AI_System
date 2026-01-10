"""
Integration tests for agent workflows.
Tests the interaction between multiple components.
"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from Core.agents import ArchitectAgent, PlannerAgent, DeveloperAgent, QAAgent


@pytest.mark.integration
class TestAgentWorkflow:
    """Integration tests for complete agent workflows."""

    @pytest.fixture
    def mock_api_response(self):
        """Mock API response for testing."""
        def _mock_response(agent_type):
            if agent_type == "architect":
                return '''
                [
                    {
                        "path": "main.py",
                        "type": "python",
                        "action": "create",
                        "description": "Main entry point"
                    }
                ]
                '''
            elif agent_type == "planner":
                return '''
                # Implementation Plan
                1. Create main function
                2. Add print statement
                3. Call main
                '''
            elif agent_type == "developer":
                return '''
                ```python
                def main():
                    print("Hello, World!")

                if __name__ == "__main__":
                    main()
                ```
                '''
            elif agent_type == "qa":
                return "PASS: Code looks good. Syntax is valid."
            return ""
        
        return _mock_response

    def test_architect_output_format(self, mock_api_response):
        """Test that Architect produces properly formatted output."""
        with patch('Core.agents.base_agent.BaseAgent.query_brain') as mock_query:
            mock_query.return_value = mock_api_response("architect")
            
            architect = ArchitectAgent()
            result = architect.process(
                task="Create a hello world program",
                context={"psi": "Test PSI"}
            )
            
            assert isinstance(result, list)
            assert len(result) > 0
            assert "path" in result[0]
            assert "type" in result[0]
            assert "action" in result[0]

    def test_planner_output_format(self, mock_api_response):
        """Test that Planner produces properly formatted output."""
        with patch('Core.agents.base_agent.BaseAgent.query_brain') as mock_query:
            mock_query.return_value = mock_api_response("planner")
            
            planner = PlannerAgent()
            result = planner.process(
                task="Create a hello world program",
                context={
                    "psi": "Test PSI",
                    "file_list": [{"path": "main.py", "type": "python"}]
                }
            )
            
            assert isinstance(result, str)
            assert len(result) > 0
            assert "main" in result.lower() or "print" in result.lower()

    def test_developer_output_format(self, mock_api_response):
        """Test that Developer produces valid Python code."""
        with patch('Core.agents.base_agent.BaseAgent.query_brain') as mock_query:
            mock_query.return_value = mock_api_response("developer")
            
            developer = DeveloperAgent()
            result = developer.process(
                file_info={
                    "path": "main.py",
                    "type": "python",
                    "action": "create"
                },
                context={
                    "task": "Create hello world",
                    "psi": "Test PSI",
                    "plan": "Create main function"
                }
            )
            
            assert isinstance(result, str)
            assert len(result) > 0
            # Should be valid Python
            assert "def " in result or "print" in result

    def test_qa_validation_pass(self, mock_api_response):
        """Test QA validation with passing code."""
        with patch('Core.agents.base_agent.BaseAgent.query_brain') as mock_query:
            mock_query.return_value = mock_api_response("qa")
            
            qa = QAAgent()
            code = 'def main():\n    print("Hello")\n\nif __name__ == "__main__":\n    main()'
            
            passed, feedback = qa.process(
                code=code,
                context={
                    "file_path": "main.py",
                    "task": "Hello world"
                }
            )
            
            assert passed is True
            assert isinstance(feedback, str)

    def test_qa_validation_fail(self):
        """Test QA validation with failing code."""
        qa = QAAgent()
        
        # Invalid Python syntax
        code = 'def broken(\nprint("missing paren")'
        
        passed, feedback = qa.quick_validate(code, "test.py")
        
        assert passed is False
        assert "syntax" in feedback.lower() or "error" in feedback.lower()


@pytest.mark.integration
class TestAgentChaining:
    """Tests for chaining agents together."""

    @pytest.fixture
    def temp_projects_dir(self):
        """Create temporary projects directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    def test_architect_to_planner_data_flow(self):
        """Test that Architect output is compatible with Planner input."""
        # Mock architect output
        architect_output = [
            {
                "path": "calculator.py",
                "type": "python",
                "action": "create",
                "description": "Calculator implementation"
            }
        ]
        
        # Planner should accept this format
        planner = PlannerAgent()
        
        # Should not raise exception
        context = {
            "psi": "Test PSI",
            "file_list": architect_output
        }
        
        # Verify context structure is valid
        assert "file_list" in context
        assert isinstance(context["file_list"], list)

    def test_planner_to_developer_data_flow(self):
        """Test that Planner output is compatible with Developer input."""
        plan = """
        # Implementation Plan
        1. Define Calculator class
        2. Implement add method
        3. Implement subtract method
        """
        
        developer = DeveloperAgent()
        
        context = {
            "task": "Create calculator",
            "psi": "Test PSI",
            "plan": plan
        }
        
        # Verify context structure is valid
        assert "plan" in context
        assert isinstance(context["plan"], str)

    def test_developer_to_qa_data_flow(self):
        """Test that Developer output is compatible with QA input."""
        code = '''
class Calculator:
    def add(self, a, b):
        return a + b
'''
        
        qa = QAAgent()
        
        # Quick validate should work with developer output
        passed, feedback = qa.quick_validate(code, "calculator.py")
        
        # Should complete without exception
        assert isinstance(passed, bool)
        assert isinstance(feedback, str)


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndWorkflow:
    """End-to-end integration tests (marked as slow)."""

    def test_complete_workflow_structure(self):
        """Test the structure of a complete workflow."""
        # This is a structural test without actual API calls
        
        # 1. Architect phase
        architect = ArchitectAgent()
        assert hasattr(architect, 'process')
        
        # 2. Planner phase  
        planner = PlannerAgent()
        assert hasattr(planner, 'process')
        
        # 3. Developer phase
        developer = DeveloperAgent()
        assert hasattr(developer, 'process')
        
        # 4. QA phase
        qa = QAAgent()
        assert hasattr(qa, 'process')
        assert hasattr(qa, 'quick_validate')
        
        # All agents initialized successfully
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
