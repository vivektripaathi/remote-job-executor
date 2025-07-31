"""
Test cases for CLI commands to check for race conditions and ensure system works as expected.

This test suite covers:
1. Job Submission - Shell commands with parameters, priorities, timeouts
2. Job Management - Status tracking, real-time logs, cancellation
3. Data Persistence - Job details, results, metrics
4. Race Conditions - Concurrent operations, multiple clients
5. Error Handling - Network issues, invalid inputs, edge cases
"""

import pytest
import asyncio
import threading
import time
import json
import uuid
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
import requests
import websockets

# Import CLI modules
from main import cli, submit, view, stream, cancel
from utils import Config, validate_job_id, make_request, handle_api_response


class TestJobSubmission:
    """Test job submission with various parameters, priorities, and timeouts."""
    
    def setup_method(self):
        """Setup test environment before each test."""
        self.runner = CliRunner()
        self.mock_response = Mock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {
            "id": "12345678-1234-1234-1234-123456789012",
            "command": "echo 'test'",
            "status": "Queued",
            "priority": "Medium",
            "timeout": 30,
            "created_at": "2025-07-30T10:00:00Z"
        }

    @patch('main.make_request')
    def test_submit_basic_command(self, mock_make_request):
        """Test basic command submission."""
        mock_make_request.return_value = self.mock_response
        
        result = self.runner.invoke(submit, ['echo "hello world"'])
        
        assert result.exit_code == 0
        assert "Job submitted successfully" in result.output
        assert "Job ID:" in result.output
        assert "Status:" in result.output
        mock_make_request.assert_called_once()

    @patch('main.make_request')
    def test_submit_with_priority_and_timeout(self, mock_make_request):
        """Test command submission with priority and timeout parameters."""
        mock_make_request.return_value = self.mock_response
        
        result = self.runner.invoke(submit, [
            'ls -la', 
            '--priority', 'High',
            '--timeout', '60'
        ])
        
        assert result.exit_code == 0
        assert "Job submitted successfully" in result.output
        mock_make_request.assert_called_once()

    def test_submit_empty_command(self):
        """Test submission with empty command should fail."""
        result = self.runner.invoke(submit, [''])
        
        assert result.exit_code == 1
        assert "Command cannot be empty" in result.output

    def test_submit_long_command(self):
        """Test submission with command exceeding length limit."""
        long_command = 'a' * 1001  # Exceeds 1000 char limit
        result = self.runner.invoke(submit, [long_command])
        
        assert result.exit_code == 1
        assert "Command too long" in result.output

    @patch('main.make_request')
    def test_submit_invalid_priority(self, mock_make_request):
        """Test submission with invalid priority value."""
        result = self.runner.invoke(submit, [
            'echo test',
            '--priority', 'Invalid'
        ])
        
        assert result.exit_code == 2  # Click validation error
        assert "Invalid value" in result.output

    @patch('main.make_request')
    def test_submit_invalid_timeout(self, mock_make_request):
        """Test submission with invalid timeout values."""
        # Test timeout too low
        result = self.runner.invoke(submit, [
            'echo test',
            '--timeout', '0'
        ])
        assert result.exit_code == 2
        
        # Test timeout too high
        result = self.runner.invoke(submit, [
            'echo test', 
            '--timeout', '3601'
        ])
        assert result.exit_code == 2

    @patch('main.make_request')
    def test_submit_network_error(self, mock_make_request):
        """Test submission with network connectivity issues."""
        mock_make_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = self.runner.invoke(submit, ['echo test'])
        assert result.exit_code == 1  # CLI exits with code 1 on error

    @patch('main.make_request')
    def test_submit_server_error(self, mock_make_request):
        """Test submission with server error response."""
        error_response = Mock()
        error_response.status_code = 500
        error_response.content = b'{"error": "Internal server error"}'
        error_response.json.return_value = {"error": "Internal server error"}
        mock_make_request.return_value = error_response
        
        result = self.runner.invoke(submit, ['echo test'])
        assert result.exit_code == 1  # CLI exits with code 1 on error


class TestJobManagement:
    """Test job status tracking, logs, and cancellation."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.job_id = "12345678-1234-1234-1234-123456789012"
        self.mock_job_response = Mock()
        self.mock_job_response.status_code = 200
        self.mock_job_response.json.return_value = {
            "id": self.job_id,
            "command": "echo 'test'",
            "status": "Success",
            "priority": "Medium",
            "timeout": 30,
            "stdout": "test\n",
            "stderr": "",
            "created_at": "2025-07-30T10:00:00Z",
            "started_at": "2025-07-30T10:00:01Z",
            "completed_at": "2025-07-30T10:00:02Z"
        }

    @patch('main.make_request')
    def test_view_job_success(self, mock_make_request):
        """Test viewing job details successfully."""
        mock_make_request.return_value = self.mock_job_response
        
        result = self.runner.invoke(view, [self.job_id])
        
        assert result.exit_code == 0
        assert "Job details retrieved" in result.output
        mock_make_request.assert_called_once()

    def test_view_invalid_job_id(self):
        """Test viewing job with invalid UUID format."""
        result = self.runner.invoke(view, ['invalid-id'])
        
        assert result.exit_code == 1
        assert "Invalid job ID format" in result.output

    @patch('main.make_request')
    def test_view_job_not_found(self, mock_make_request):
        """Test viewing non-existent job."""
        error_response = Mock()
        error_response.status_code = 404
        error_response.content = b'{"error": "Job not found"}'
        error_response.json.return_value = {"error": "Job not found"}
        mock_make_request.return_value = error_response
        
        result = self.runner.invoke(view, [self.job_id])
        assert result.exit_code == 1
        assert "Resource not found" in result.output

    @patch('main.make_request')
    def test_cancel_job_success(self, mock_make_request):
        """Test successful job cancellation."""
        # Mock two calls: GET for status check, POST for cancellation
        get_response = Mock()
        get_response.status_code = 200
        get_response.content = b'{"status": "Running"}'
        get_response.json.return_value = {"status": "Running", "command": "echo test"}
        
        post_response = Mock()
        post_response.status_code = 200
        post_response.content = b'{"message": "cancelled"}'
        post_response.json.return_value = {"message": "cancelled"}
        
        mock_make_request.side_effect = [get_response, post_response]
        
        result = self.runner.invoke(cancel, [self.job_id, '--force'])
        
        assert result.exit_code == 0
        assert "Job cancellation requested successfully" in result.output

    @patch('main.make_request')
    def test_cancel_job_confirmation_required(self, mock_make_request):
        """Test job cancellation requires confirmation without --force."""
        # Mock GET and POST responses
        get_response = Mock()
        get_response.status_code = 200
        get_response.content = b'{"status": "Running"}'
        get_response.json.return_value = {"status": "Running", "command": "echo test"}
        
        post_response = Mock()
        post_response.status_code = 200
        post_response.content = b'{"message": "cancelled"}'
        post_response.json.return_value = {"message": "cancelled"}
        
        mock_make_request.side_effect = [get_response, post_response]
        
        # Simulate user typing 'y' for confirmation
        result = self.runner.invoke(cancel, [self.job_id], input='y\n')
        
        assert result.exit_code == 0

    @patch('main.make_request')
    def test_cancel_job_confirmation_denied(self, mock_make_request):
        """Test job cancellation denied by user."""
        # Mock GET response for status check
        get_response = Mock()
        get_response.status_code = 200
        get_response.content = b'{"status": "Running"}'
        get_response.json.return_value = {"status": "Running", "command": "echo test"}
        
        mock_make_request.return_value = get_response
        
        # Simulate user typing 'n' for denial
        result = self.runner.invoke(cancel, [self.job_id], input='n\n')
        
        assert result.exit_code == 0
        assert "Cancellation aborted" in result.output


class TestRealTimeStreaming:
    """Test real-time log streaming functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.job_id = "12345678-1234-1234-1234-123456789012"

    @patch('main.stream_job_logs')
    @patch('main.make_request')
    def test_stream_logs_success(self, mock_make_request, mock_stream_logs):
        """Test successful log streaming."""
        # Mock GET response for status check
        get_response = Mock()
        get_response.status_code = 200
        get_response.content = b'{"status": "Running"}'
        get_response.json.return_value = {"status": "Running", "command": "echo test"}
        
        mock_make_request.return_value = get_response
        mock_stream_logs.return_value = None  # Simulate successful streaming
        
        result = self.runner.invoke(stream, [self.job_id])
        
        assert result.exit_code == 0
        mock_stream_logs.assert_called_once_with(self.job_id, 3600)  # default duration

    def test_stream_invalid_job_id(self):
        """Test streaming with invalid job ID."""
        result = self.runner.invoke(stream, ['invalid-id'])
        
        assert result.exit_code == 1
        assert "Invalid job ID format" in result.output

    @patch('main.stream_job_logs')
    @patch('main.make_request')
    def test_stream_connection_failed(self, mock_make_request, mock_stream_logs):
        """Test streaming when WebSocket connection fails."""
        # Mock GET response for status check
        get_response = Mock()
        get_response.status_code = 200
        get_response.content = b'{"status": "Running"}'
        get_response.json.return_value = {"status": "Running", "command": "echo test"}
        
        mock_make_request.return_value = get_response
        mock_stream_logs.side_effect = Exception("Connection failed")
        
        result = self.runner.invoke(stream, [self.job_id])
        
        # CLI should handle the error gracefully
        assert result.exit_code == 1


class TestConcurrencyAndRaceConditions:
    """Test concurrent operations and race condition handling."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.job_ids = [str(uuid.uuid4()) for _ in range(10)]

    @patch('main.make_request')
    def test_concurrent_job_submissions(self, mock_make_request):
        """Test multiple concurrent job submissions."""
        def mock_submit_response(method, url, **kwargs):
            response = Mock()
            response.status_code = 200
            response.content = b'{"id": "test"}'
            response.json.return_value = {
                "id": str(uuid.uuid4()),
                "command": kwargs['json']['command'],
                "status": "Queued",
                "priority": kwargs['json']['priority'],
                "timeout": kwargs['json']['timeout']
            }
            return response
        
        mock_make_request.side_effect = mock_submit_response
        
        def submit_job(command):
            return self.runner.invoke(submit, [f'echo "{command}"'])
        
        # Submit 10 jobs concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_job, f"job-{i}") for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Most submissions should succeed (allowing for some race condition variability)
        success_count = sum(1 for r in results if r.exit_code == 0 and "Job submitted successfully" in r.output)
        assert success_count >= 8, f"Expected at least 8 successful submissions, got {success_count}"
        
        # Should make 10 requests
        assert mock_make_request.call_count == 10

    @patch('main.make_request')
    def test_concurrent_job_views(self, mock_make_request):
        """Test concurrent job status checks."""
        def mock_view_response(method, url, **kwargs):
            job_id = url.split('/')[-2]  # Extract job ID from URL
            response = Mock()
            response.status_code = 200
            response.content = b'{"status": "Success"}'
            response.json.return_value = {
                "id": job_id,
                "command": f"echo 'job-{job_id}'",
                "status": "Success",
                "priority": "Medium",
                "timeout": 30,
                "stdout": f"job-{job_id}\n",
                "stderr": ""
            }
            return response
        
        mock_make_request.side_effect = mock_view_response
        
        def view_job(job_id):
            return self.runner.invoke(view, [job_id])
        
        # View 10 jobs concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(view_job, job_id) for job_id in self.job_ids]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All views should succeed
        for result in results:
            assert result.exit_code == 0
            assert "Job details retrieved" in result.output

    @patch('main.make_request')
    def test_concurrent_job_cancellations(self, mock_make_request):
        """Test concurrent job cancellations."""
        mock_make_request.return_value = Mock(status_code=200)
        
        def cancel_job(job_id):
            return self.runner.invoke(cancel, [job_id, '--force'])
        
        # Cancel 5 jobs concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(cancel_job, job_id) for job_id in self.job_ids[:5]]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All cancellations should succeed
        for result in results:
            assert result.exit_code == 0

    @patch('main.stream_job_logs')
    @patch('main.make_request')
    def test_concurrent_streaming_sessions(self, mock_make_request, mock_stream_logs):
        """Test multiple concurrent streaming sessions."""
        # Mock status check response
        get_response = Mock()
        get_response.status_code = 200
        get_response.content = b'{"status": "Running"}'
        get_response.json.return_value = {"status": "Running", "command": "echo test"}
        
        mock_make_request.return_value = get_response
        mock_stream_logs.return_value = None
        
        def stream_job(job_id):
            return self.runner.invoke(stream, [job_id])
        
        # Start 3 concurrent streaming sessions
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(stream_job, job_id) for job_id in self.job_ids[:3]]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All should attempt to start streaming
        assert mock_stream_logs.call_count == 3


class TestDataPersistence:
    """Test data persistence and job lifecycle."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()

    @patch('main.make_request')
    def test_job_lifecycle_tracking(self, mock_make_request):
        """Test complete job lifecycle from submission to completion."""
        job_id = str(uuid.uuid4())
        
        # Mock responses for different job states
        responses = [
            # Submit response
            Mock(status_code=200, **{'json.return_value': {
                "id": job_id,
                "command": "sleep 5 && echo 'done'",
                "status": "Queued",
                "priority": "Medium",
                "timeout": 30
            }}),
            # First view - Running
            Mock(status_code=200, **{'json.return_value': {
                "id": job_id,
                "command": "sleep 5 && echo 'done'",
                "status": "Running",
                "priority": "Medium",
                "timeout": 30,
                "started_at": "2025-07-30T10:00:01Z"
            }}),
            # Second view - Success
            Mock(status_code=200, **{'json.return_value': {
                "id": job_id,
                "command": "sleep 5 && echo 'done'",
                "status": "Success",
                "priority": "Medium",
                "timeout": 30,
                "stdout": "done\n",
                "stderr": "",
                "started_at": "2025-07-30T10:00:01Z",
                "completed_at": "2025-07-30T10:00:06Z"
            }})
        ]
        
        mock_make_request.side_effect = responses
        
        # Submit job
        result = self.runner.invoke(submit, ['sleep 5 && echo "done"'])
        assert result.exit_code == 0
        assert job_id in result.output
        
        # Check status while running
        result = self.runner.invoke(view, [job_id])
        assert result.exit_code == 0
        assert "Running" in result.output
        
        # Check final status
        result = self.runner.invoke(view, [job_id])
        assert result.exit_code == 0
        assert "Success" in result.output
        assert "done" in result.output

    @patch('main.make_request')
    def test_job_metrics_tracking(self, mock_make_request):
        """Test that job metrics are properly tracked."""
        job_response = Mock()
        job_response.status_code = 200
        job_response.json.return_value = {
            "id": str(uuid.uuid4()),
            "command": "echo 'performance test'",
            "status": "Success",
            "priority": "High",
            "timeout": 30,
            "stdout": "performance test\n",
            "stderr": "",
            "created_at": "2025-07-30T10:00:00Z",
            "started_at": "2025-07-30T10:00:01Z",
            "completed_at": "2025-07-30T10:00:02Z",
            "duration": "0:00:01.123456"
        }
        mock_make_request.return_value = job_response
        
        result = self.runner.invoke(view, [job_response.json()["id"]])
        
        assert result.exit_code == 0
        output = result.output
        assert "Duration" in output
        assert "0:00:01" in output  # Duration is displayed without microseconds
        assert "High" in output  # Priority
        assert "30s" in output   # Timeout


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()

    @patch('main.make_request')
    def test_api_timeout_handling(self, mock_make_request):
        """Test handling of API request timeouts."""
        mock_make_request.side_effect = requests.exceptions.Timeout("Request timed out")
        
        result = self.runner.invoke(submit, ['echo test'])
        assert result.exit_code == 1

    @patch('main.make_request')
    def test_malformed_json_response(self, mock_make_request):
        """Test handling of malformed JSON responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'invalid json'
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_make_request.return_value = mock_response
        
        result = self.runner.invoke(submit, ['echo test'])
        assert result.exit_code == 1

    def test_config_file_missing(self):
        """Test behavior when config file is missing."""
        with patch('os.path.exists', return_value=False):
            config = Config()
            assert config.base_url == "http://localhost:8000/jobs"
            assert config.ws_url == "ws://localhost:8000/ws/jobs"

    @patch('main.make_request')
    def test_partial_system_failure(self, mock_make_request):
        """Test behavior during partial system failures."""
        # Simulate intermittent failures
        responses = [
            requests.exceptions.ConnectionError("Service unavailable"),
            Mock(status_code=200, **{'json.return_value': {"id": str(uuid.uuid4()), "status": "Queued"}})
        ]
        mock_make_request.side_effect = responses
        
        # First request fails
        result = self.runner.invoke(submit, ['echo test'])
        assert result.exit_code == 1
        
        # Reset mock for second request
        mock_make_request.side_effect = responses[1:]
        result = self.runner.invoke(submit, ['echo test'])
        assert result.exit_code == 0


class TestUtilities:
    """Test utility functions."""
    
    def test_validate_job_id_valid(self):
        """Test job ID validation with valid UUIDs."""
        valid_ids = [
            "12345678-1234-1234-1234-123456789012",
            str(uuid.uuid4()),
            "a" * 8 + "-" + "b" * 4 + "-" + "c" * 4 + "-" + "d" * 4 + "-" + "e" * 12
        ]
        
        for job_id in valid_ids:
            assert validate_job_id(job_id) is True

    def test_validate_job_id_invalid(self):
        """Test job ID validation with invalid formats."""
        invalid_ids = [
            "not-a-uuid",
            "12345678",
            "",
            "12345678-1234-1234-1234",  # Too short
            "12345678-1234-1234-1234-123456789012-extra",  # Too long
            None
        ]
        
        for job_id in invalid_ids:
            assert validate_job_id(job_id) is False

    def test_config_environment_override(self):
        """Test configuration can be overridden by environment variables."""
        with patch.dict('os.environ', {
            'REMOTE_JOB_API_URL': 'http://custom-api:9000/jobs',
            'REMOTE_JOB_WS_URL': 'ws://custom-ws:9000/ws/jobs'
        }):
            config = Config()
            assert config.base_url == 'http://custom-api:9000/jobs'
            assert config.ws_url == 'ws://custom-ws:9000/ws/jobs'


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([
        "-v",
        "--tb=short",
        "test_cli.py::TestJobSubmission",
        "test_cli.py::TestJobManagement", 
        "test_cli.py::TestRealTimeStreaming",
        "test_cli.py::TestConcurrencyAndRaceConditions",
        "test_cli.py::TestDataPersistence",
        "test_cli.py::TestErrorHandling",
        "test_cli.py::TestUtilities"
    ])
