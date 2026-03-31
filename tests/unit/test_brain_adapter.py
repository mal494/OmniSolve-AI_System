"""
Unit tests for Core.brain adapter layer.
Tests MockBrainAPI, factory, KoboldBrainAPI request format, and token tracking.
"""
import pytest
from unittest.mock import patch, MagicMock

from Core.brain import BrainAPI, GenerateResult, MockBrainAPI, create_brain
from Core.brain.base_brain import BrainAPI as BrainAPIBase
from Core.brain.factory import create_brain
from Core.exceptions.errors import ConfigurationError


class TestMockBrainAPI:
    """Tests for MockBrainAPI — the test double for all LLM backends."""

    def test_is_available_always_true(self):
        brain = MockBrainAPI()
        assert brain.is_available() is True

    def test_generate_returns_generate_result(self):
        brain = MockBrainAPI()
        result = brain.generate(
            prompt="tell me about the architect",
            temperature=0.3,
            max_length=512,
            max_context=2048,
            stop_tokens=[],
        )
        assert isinstance(result, GenerateResult)
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        assert result.model == "mock"

    def test_generate_keyword_routing(self):
        """Mock picks the response whose key appears in the prompt."""
        responses = {
            "architect": "ARCHITECT RESPONSE",
            "developer": "DEVELOPER RESPONSE",
            "default": "DEFAULT RESPONSE",
        }
        brain = MockBrainAPI(responses=responses)

        result = brain.generate("architect task", 0.3, 512, 2048, [])
        assert result.text == "ARCHITECT RESPONSE"

        result = brain.generate("developer task", 0.3, 512, 2048, [])
        assert result.text == "DEVELOPER RESPONSE"

        result = brain.generate("something else entirely", 0.3, 512, 2048, [])
        assert result.text == "DEFAULT RESPONSE"

    def test_generate_records_call_log(self):
        call_log = []
        brain = MockBrainAPI(call_log=call_log)
        brain.generate("test prompt", 0.5, 100, 1024, [])
        assert len(call_log) == 1
        assert call_log[0]["temperature"] == 0.5
        assert call_log[0]["max_length"] == 100

    def test_tokens_used_is_set(self):
        brain = MockBrainAPI({"default": "hello"})
        result = brain.generate("anything", 0.3, 512, 2048, [])
        # Tokens used = word count of response
        assert result.tokens_used is not None
        assert result.tokens_used > 0

    def test_implements_brain_api(self):
        brain = MockBrainAPI()
        assert isinstance(brain, BrainAPIBase)


class TestBrainFactory:
    """Tests for create_brain() factory function."""

    def test_create_mock_backend(self):
        brain = create_brain("mock")
        assert isinstance(brain, MockBrainAPI)
        assert brain.is_available() is True

    def test_unknown_backend_raises(self):
        with pytest.raises(ConfigurationError, match="Unknown brain backend"):
            create_brain("unicorn")

    def test_default_backend_is_kobold(self):
        """Default backend creates KoboldBrainAPI (no connection needed for init)."""
        from Core.brain.kobold_brain import KoboldBrainAPI
        brain = create_brain("kobold")
        assert isinstance(brain, KoboldBrainAPI)


class TestKoboldBrainAPI:
    """Tests for KoboldBrainAPI — verifies request format and response parsing."""

    def _make_mock_response(self, text="Hello from Kobold", status=200):
        mock_resp = MagicMock()
        mock_resp.status_code = status
        mock_resp.json.return_value = {"results": [{"text": text}]}
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    def test_generate_sends_correct_payload(self):
        from Core.brain.kobold_brain import KoboldBrainAPI
        brain = KoboldBrainAPI(api_url="http://localhost:5001/api/v1/generate")

        with patch("requests.post") as mock_post:
            mock_post.return_value = self._make_mock_response("test output")
            result = brain.generate(
                prompt="hello",
                temperature=0.4,
                max_length=256,
                max_context=1024,
                stop_tokens=["STOP"],
            )

        assert result.text == "test output"
        assert result.model == "koboldcpp"

        call_kwargs = mock_post.call_args
        payload = call_kwargs[1]["json"] if call_kwargs[1] else call_kwargs[0][1]
        assert payload["prompt"] == "hello"
        assert payload["temperature"] == 0.4
        assert payload["max_length"] == 256
        assert payload["stop_sequence"] == ["STOP"]

    def test_generate_parses_token_usage(self):
        from Core.brain.kobold_brain import KoboldBrainAPI
        brain = KoboldBrainAPI()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"text": "response text"}],
            "usage": {"completion_tokens": 42},
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp):
            result = brain.generate("prompt", 0.3, 512, 2048, [])

        assert result.tokens_used == 42

    def test_generate_connection_error_raises(self):
        import requests as req
        from Core.brain.kobold_brain import KoboldBrainAPI
        from Core.exceptions.errors import BrainConnectionError
        brain = KoboldBrainAPI()

        with patch("requests.post", side_effect=req.exceptions.ConnectionError("refused")):
            with pytest.raises(BrainConnectionError):
                brain.generate("prompt", 0.3, 512, 2048, [])

    def test_generate_timeout_raises(self):
        import requests as req
        from Core.brain.kobold_brain import KoboldBrainAPI
        from Core.exceptions.errors import BrainConnectionError
        brain = KoboldBrainAPI()

        with patch("requests.post", side_effect=req.exceptions.Timeout("timeout")):
            with pytest.raises(BrainConnectionError):
                brain.generate("prompt", 0.3, 512, 2048, [])

    def test_generate_empty_response_raises(self):
        from Core.brain.kobold_brain import KoboldBrainAPI
        from Core.exceptions.errors import BrainResponseError
        brain = KoboldBrainAPI()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": [{"text": "   "}]}
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(BrainResponseError):
                brain.generate("prompt", 0.3, 512, 2048, [])

    def test_generate_missing_results_key_raises(self):
        from Core.brain.kobold_brain import KoboldBrainAPI
        from Core.exceptions.errors import BrainResponseError
        brain = KoboldBrainAPI()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"output": "wrong key"}
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(BrainResponseError):
                brain.generate("prompt", 0.3, 512, 2048, [])


class TestGenerateResult:
    """Tests for the GenerateResult dataclass."""

    def test_defaults(self):
        r = GenerateResult(text="hello")
        assert r.text == "hello"
        assert r.tokens_used is None
        assert r.model is None

    def test_with_all_fields(self):
        r = GenerateResult(text="hi", tokens_used=10, model="gpt-4o")
        assert r.tokens_used == 10
        assert r.model == "gpt-4o"
