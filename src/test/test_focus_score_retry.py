"""
Unit tests for FocusScoreService retry behavior
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import openai
from fastapi import HTTPException

from src.services.focus_score_service import FocusScoreService
from src.config.settings import FocusScoreSettings
from src.models.focus_models import FocusScoreResponse


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client"""
    return AsyncMock(spec=openai.AsyncOpenAI)


@pytest.fixture
def default_settings():
    """Create default settings for testing"""
    return FocusScoreSettings(
        openai_api_key="sk-test-key-for-testing",
        model_id="gpt-4o-mini",
        max_retries=3,
        retry_delay_seconds=1,  # Short delay for testing
        test_mode=True
    )


@pytest.fixture
def custom_retry_settings():
    """Create settings with custom retry configuration"""
    return FocusScoreSettings(
        openai_api_key="sk-test-key-for-testing",
        model_id="gpt-4o-mini",
        max_retries=5,
        retry_delay_seconds=2,
        test_mode=True
    )


class TestFocusScoreServiceRetry:
    """Test retry behavior of FocusScoreService"""
    
    def test_init_stores_retry_config(self, mock_openai_client, custom_retry_settings):
        """Test that __init__ stores retry configuration from settings"""
        service = FocusScoreService(mock_openai_client, custom_retry_settings)
        
        assert service.max_retries == 5
        assert service.retry_delay_seconds == 2
        assert service.settings.max_retries == 5
        assert service.settings.retry_delay_seconds == 2
    
    @pytest.mark.asyncio
    async def test_successful_first_attempt(self, mock_openai_client, default_settings):
        """Test successful analysis on first attempt (no retries needed)"""
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.model_dump.return_value = {
            'content': '{"focus_score": 85}'
        }
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Mock the pydantic parsing (兼容v1/v2)
        with patch.object(FocusScoreResponse, 'model_validate', return_value=FocusScoreResponse(
            focus_score=85,
            confidence="high",
            processing_time=0.1
        )) as mock_validate:
            
            service = FocusScoreService(mock_openai_client, default_settings)
            score, processing_time = await service.analyze_image_base64("fake_base64")
            
            assert score == 85
            assert processing_time > 0
            # Should only call once (no retries)
            assert mock_openai_client.chat.completions.create.call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_generic_exception(self, mock_openai_client, default_settings):
        """Test retry behavior on generic exceptions"""
        # First 2 calls fail, 3rd succeeds
        mock_success_response = Mock()
        mock_success_response.choices = [Mock()]  
        mock_success_response.choices[0].message.model_dump.return_value = {'content': '{"focus_score": 75}'}
        
        mock_openai_client.chat.completions.create = AsyncMock(side_effect=[
            Exception("Network error"),
            Exception("Timeout error"),
            mock_success_response
        ])
        
        with patch.object(FocusScoreResponse, 'model_validate', return_value=FocusScoreResponse(
            focus_score=75,
            confidence="high", 
            processing_time=0.1
        )) as mock_validate:
            
            with patch('asyncio.sleep') as mock_sleep:  # Speed up test
                service = FocusScoreService(mock_openai_client, default_settings)
                score, processing_time = await service.analyze_image_base64("fake_base64")
                
                assert score == 75
                # Should have called 3 times (2 failures + 1 success)
                assert mock_openai_client.chat.completions.create.call_count == 3
                # Should have slept 2 times (after first 2 failures)
                assert mock_sleep.call_count == 2
    
    @pytest.mark.asyncio
    async def test_no_retry_on_openai_api_error(self, mock_openai_client, default_settings):
        """Test that OpenAI API errors are not retried"""
        from fastapi import HTTPException
        
        # Mock OpenAI API error (简单方式，测试重点是不重试)
        mock_openai_client.chat.completions.create.side_effect = openai.APIError(
            message="API key invalid", 
            request=Mock(),
            body=None
        )
        
        service = FocusScoreService(mock_openai_client, default_settings)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.analyze_image_base64("fake_base64")
        
        assert exc_info.value.status_code == 502
        assert "External API service error" in str(exc_info.value.detail)
        # Should only call once (no retries for API errors)
        assert mock_openai_client.chat.completions.create.call_count == 1
    
    @pytest.mark.asyncio
    async def test_custom_retry_configuration(self, mock_openai_client, custom_retry_settings):
        """Test that custom retry settings are respected"""
        # All calls fail to test max_retries
        mock_openai_client.chat.completions.create.side_effect = Exception("Always fails")
        
        from fastapi import HTTPException
        
        with patch('asyncio.sleep') as mock_sleep:
            service = FocusScoreService(mock_openai_client, custom_retry_settings)
            
            with pytest.raises(HTTPException) as exc_info:
                await service.analyze_image_base64("fake_base64")
            
            assert exc_info.value.status_code == 500
            # Should have called max_retries+1 times (5+1=6)
            assert mock_openai_client.chat.completions.create.call_count == 6
            # Should have slept 5 times (after first 5 failures)
            assert mock_sleep.call_count == 5
            
            # Check exponential backoff with custom delay
            expected_delays = [2, 4, 8, 16, 32]  # retry_delay_seconds * (2 ** attempt)
            actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
            assert actual_delays == expected_delays
    
    @pytest.mark.asyncio
    async def test_zero_retries_configuration(self, mock_openai_client):
        """Test with zero retries configuration"""
        settings = FocusScoreSettings(
            openai_api_key="sk-test-key-for-testing",
            max_retries=0,
            retry_delay_seconds=1,
            test_mode=True
        )
        
        mock_openai_client.chat.completions.create.side_effect = Exception("Network error")
        
        from fastapi import HTTPException
        
        service = FocusScoreService(mock_openai_client, settings)
        
        with pytest.raises(HTTPException):
            await service.analyze_image_base64("fake_base64")
        
        # Should only call once (no retries when max_retries=0)
        assert mock_openai_client.chat.completions.create.call_count == 1
    
    @pytest.mark.asyncio
    async def test_health_check_includes_retry_settings(self, mock_openai_client, custom_retry_settings):
        """Test that health check includes retry configuration"""
        mock_openai_client.models.list.return_value = ["model1", "model2"]
        
        service = FocusScoreService(mock_openai_client, custom_retry_settings)
        health = await service.health_check()
        
        assert health["settings"]["max_retries"] == 5
        assert "max_retries" in health["settings"]
    
    @pytest.mark.asyncio  
    async def test_safe_response_parsing(self, mock_openai_client, default_settings):
        """Test improved response parsing with validation"""
        # Test empty choices array
        mock_response = Mock()
        mock_response.choices = []
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        service = FocusScoreService(mock_openai_client, default_settings)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.analyze_image_base64("fake_base64")
        
        assert exc_info.value.status_code == 500
        assert "Internal processing error" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_pydantic_version_compatibility(self, mock_openai_client, default_settings):
        """Test Pydantic v1/v2 compatibility"""
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.model_dump.return_value = {
            'content': '{"focus_score": 90}'
        }
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        service = FocusScoreService(mock_openai_client, default_settings)
        
        # Test v2 method exists (should work normally)
        assert hasattr(FocusScoreResponse, 'model_validate')
        
        with patch.object(FocusScoreResponse, 'model_validate', return_value=FocusScoreResponse(
            focus_score=90,
            confidence="high",
            processing_time=0.1
        )):
            score, processing_time = await service.analyze_image_base64("fake_base64")
            assert score == 90
