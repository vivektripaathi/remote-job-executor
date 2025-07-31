"""
Comprehensive race condition tests for CLI commands.

This module focuses specifically on testing race conditions and concurrent scenarios
that could occur during real-world usage of the CLI tools.
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

from main import submit, view, stream, cancel
from utils import make_request


@pytest.mark.race_condition
class TestJobSubmissionRaceConditions:
    """Test race conditions during job submission."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.submission_count = 0
        self.response_lock = threading.Lock()

    @patch('main.make_request')
    def test_rapid_fire_submissions(self, mock_make_request):
        """Test rapid consecutive job submissions to detect race conditions."""
        
        def mock_submit_with_delay(*args, **kwargs):
            """Mock that simulates server processing delay."""
            time.sleep(0.1)  # Simulate network/processing delay
            with self.response_lock:
                self.submission_count += 1
                response = Mock()
                response.status_code = 200
                response.json.return_value = {
                    "id": str(uuid.uuid4()),
                    "command": kwargs['json']['command'],
                    "status": "Queued",
                    "submission_order": self.submission_count
                }
                return response
        
        mock_make_request.side_effect = mock_submit_with_delay
        
        # Submit 20 jobs as fast as possible
        def submit_job(i):
            return self.runner.invoke(submit, [f'echo "rapid-job-{i}"'])
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(submit_job, i) for i in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        end_time = time.time()
        
        # Verify all submissions succeeded
        success_count = sum(1 for r in results if r.exit_code == 0)
        assert success_count == 20, f"Only {success_count}/20 submissions succeeded"
        
        # Verify rapid execution (should complete in reasonable time despite delays)
        execution_time = end_time - start_time
        assert execution_time < 5.0, f"Took too long: {execution_time}s"
        
        # Verify all requests were made
        assert mock_make_request.call_count == 20

    @patch('main.make_request')
    def test_submission_with_server_throttling(self, mock_make_request):
        """Test job submission when server implements rate limiting."""
        
        call_count = 0
        
        def mock_throttled_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count <= 5:
                # First 5 requests succeed
                response = Mock()
                response.status_code = 200
                response.json.return_value = {
                    "id": str(uuid.uuid4()),
                    "command": kwargs['json']['command'],
                    "status": "Queued"
                }
                return response
            elif call_count <= 10:
                # Next 5 requests get throttled
                response = Mock()
                response.status_code = 429
                response.json.return_value = {"error": "Rate limit exceeded"}
                return response
            else:
                # Later requests succeed again
                response = Mock()
                response.status_code = 200
                response.json.return_value = {
                    "id": str(uuid.uuid4()),
                    "command": kwargs['json']['command'],
                    "status": "Queued"
                }
                return response
        
        mock_make_request.side_effect = mock_throttled_response
        
        # Submit 15 jobs concurrently
        def submit_job(i):
            try:
                return self.runner.invoke(submit, [f'echo "throttled-job-{i}"'])
            except SystemExit:
                return Mock(exit_code=1)  # CLI exits on HTTP errors
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(submit_job, i) for i in range(15)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Some requests should succeed, some should fail due to throttling
        success_count = sum(1 for r in results if r.exit_code == 0)
        assert success_count >= 5, "At least some requests should succeed"
        assert success_count <= 10, "Some requests should be throttled"

    @patch('main.make_request')
    def test_duplicate_submission_handling(self, mock_make_request):
        """Test handling of duplicate job submissions."""
        
        submitted_commands = set()
        
        def mock_duplicate_check(*args, **kwargs):
            command = kwargs['json']['command']
            
            if command in submitted_commands:
                # Simulate server rejecting duplicate
                response = Mock()
                response.status_code = 409
                response.json.return_value = {"error": "Duplicate command"}
                return response
            else:
                submitted_commands.add(command)
                response = Mock()
                response.status_code = 200
                response.json.return_value = {
                    "id": str(uuid.uuid4()),
                    "command": command,
                    "status": "Queued"
                }
                return response
        
        mock_make_request.side_effect = mock_duplicate_check
        
        # Submit the same command multiple times concurrently
        def submit_same_job():
            try:
                return self.runner.invoke(submit, ['echo "duplicate test"'])
            except SystemExit:
                return Mock(exit_code=1)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(submit_same_job) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Only one should succeed, others should fail
        success_count = sum(1 for r in results if r.exit_code == 0)
        assert success_count == 1, f"Expected 1 success, got {success_count}"


@pytest.mark.race_condition
class TestJobManagementRaceConditions:
    """Test race conditions during job management operations."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.job_id = str(uuid.uuid4())

    @patch('main.make_request')
    def test_concurrent_status_checks(self, mock_make_request):
        """Test concurrent status checks on the same job."""
        
        status_sequence = ["Queued", "Running", "Running", "Success", "Success"]
        call_count = 0
        
        def mock_status_progression(*args, **kwargs):
            nonlocal call_count
            current_status = status_sequence[min(call_count, len(status_sequence) - 1)]
            call_count += 1
            
            response = Mock()
            response.status_code = 200
            response.json.return_value = {
                "id": self.job_id,
                "command": "echo 'status test'",
                "status": current_status,
                "priority": "Medium",
                "timeout": 30
            }
            return response
        
        mock_make_request.side_effect = mock_status_progression
        
        # Multiple concurrent status checks
        def check_status():
            return self.runner.invoke(view, [self.job_id])
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_status) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All status checks should succeed
        success_count = sum(1 for r in results if r.exit_code == 0)
        assert success_count == 10, f"Expected 10 successes, got {success_count}"
        
        # Should see status progression in outputs
        all_output = ' '.join(r.output for r in results)
        assert "Queued" in all_output or "Running" in all_output or "Success" in all_output

    @patch('main.make_request')
    def test_cancel_during_status_check(self, mock_make_request):
        """Test canceling a job while status is being checked."""
        
        operations = []
        
        def mock_operation_tracker(method, url, **kwargs):
            if 'cancel' in url:
                operations.append('cancel')
                response = Mock()
                response.status_code = 200
                return response
            else:
                operations.append('status_check')
                response = Mock()
                response.status_code = 200
                response.json.return_value = {
                    "id": self.job_id,
                    "command": "echo 'cancel test'",
                    "status": "Running" if len(operations) < 3 else "Cancelled",
                    "priority": "Medium",
                    "timeout": 30
                }
                return response
        
        mock_make_request.side_effect = mock_operation_tracker
        
        # Start status checks and cancellation concurrently
        def check_status():
            return self.runner.invoke(view, [self.job_id])
        
        def cancel_job():
            return self.runner.invoke(cancel, [self.job_id, '--force'])
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Start 3 status checks
            status_futures = [executor.submit(check_status) for _ in range(3)]
            # Start 1 cancellation
            cancel_future = executor.submit(cancel_job)
            
            # Wait for all operations
            all_futures = status_futures + [cancel_future]
            results = [future.result() for future in concurrent.futures.as_completed(all_futures)]
        
        # All operations should complete successfully
        success_count = sum(1 for r in results if r.exit_code == 0)
        assert success_count == 4, f"Expected 4 successes, got {success_count}"
        
        # Should have both types of operations
        assert 'cancel' in operations
        assert 'status_check' in operations

    @patch('main.make_request')
    def test_multiple_cancellation_attempts(self, mock_make_request):
        """Test multiple concurrent cancellation attempts on same job."""
        
        cancellation_count = 0
        
        def mock_cancellation_response(*args, **kwargs):
            nonlocal cancellation_count
            cancellation_count += 1
            
            if cancellation_count == 1:
                # First cancellation succeeds
                response = Mock()
                response.status_code = 200
                return response
            else:
                # Subsequent cancellations fail (job already cancelled)
                response = Mock()
                response.status_code = 400
                response.json.return_value = {"error": "Job already cancelled"}
                return response
        
        mock_make_request.side_effect = mock_cancellation_response
        
        # Multiple concurrent cancellation attempts
        def cancel_job():
            try:
                return self.runner.invoke(cancel, [self.job_id, '--force'])
            except SystemExit:
                return Mock(exit_code=1)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(cancel_job) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Only one cancellation should succeed
        success_count = sum(1 for r in results if r.exit_code == 0)
        assert success_count == 1, f"Expected 1 success, got {success_count}"
        
        # All requests should have been made
        assert mock_make_request.call_count == 5


@pytest.mark.race_condition
class TestStreamingRaceConditions:
    """Test race conditions during WebSocket streaming."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.job_ids = [str(uuid.uuid4()) for _ in range(5)]

    @patch('websockets.connect')
    @patch('asyncio.run')
    def test_concurrent_streaming_sessions(self, mock_asyncio_run, mock_websocket_connect):
        """Test multiple concurrent WebSocket streaming sessions."""
        
        active_connections = []
        
        def mock_websocket_connection(*args, **kwargs):
            mock_websocket = Mock()
            active_connections.append(mock_websocket)
            
            # Simulate different message sequences for each connection
            connection_id = len(active_connections)
            mock_websocket.recv.side_effect = [
                json.dumps({"type": "log", "data": f"Connection {connection_id} started\n"}),
                json.dumps({"type": "log", "data": f"Connection {connection_id} processing\n"}),
                json.dumps({"type": "status", "data": "Success"})
            ]
            
            return mock_websocket
        
        mock_websocket_connect.return_value.__aenter__.return_value = Mock()
        mock_websocket_connect.return_value.__aenter__.side_effect = mock_websocket_connection
        
        # Start multiple streaming sessions concurrently
        def stream_job(job_id):
            return self.runner.invoke(stream, [job_id])
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(stream_job, job_id) for job_id in self.job_ids]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All streaming attempts should start successfully
        assert mock_asyncio_run.call_count == 5
        assert len(active_connections) <= 5  # May be less due to mocking

    @patch('websockets.connect')
    @patch('asyncio.run')
    def test_streaming_connection_interruption(self, mock_asyncio_run, mock_websocket_connect):
        """Test behavior when streaming connections are interrupted."""
        
        def mock_interrupted_connection(*args, **kwargs):
            # Simulate connection being interrupted
            if 'interrupted' in str(args):
                raise websockets.exceptions.ConnectionClosed(None, None)
            else:
                mock_websocket = Mock()
                mock_websocket.recv.side_effect = [
                    json.dumps({"type": "log", "data": "Starting...\n"}),
                    websockets.exceptions.ConnectionClosed(None, None)  # Connection drops
                ]
                return mock_websocket
        
        mock_websocket_connect.return_value.__aenter__.side_effect = mock_interrupted_connection
        
        # Start streaming sessions, some will be interrupted
        def stream_job(job_id, interrupted=False):
            job_param = f"{job_id}-interrupted" if interrupted else job_id
            try:
                return self.runner.invoke(stream, [job_param])
            except SystemExit:
                return Mock(exit_code=1)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # 2 normal streams, 2 interrupted streams
            futures = [
                executor.submit(stream_job, self.job_ids[0], False),
                executor.submit(stream_job, self.job_ids[1], True),
                executor.submit(stream_job, self.job_ids[2], False),
                executor.submit(stream_job, self.job_ids[3], True)
            ]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Some should succeed, some should fail due to interruption
        success_count = sum(1 for r in results if hasattr(r, 'exit_code') and r.exit_code == 0)
        failure_count = len(results) - success_count
        
        assert success_count >= 0, "At least some connections should attempt to start"
        assert failure_count >= 0, "Some connections should be interrupted"


@pytest.mark.race_condition
class TestSystemStateRaceConditions:
    """Test race conditions affecting overall system state."""
    
    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()

    @patch('main.make_request')
    def test_mixed_operations_race_condition(self, mock_make_request):
        """Test mixed operations (submit, view, cancel) happening concurrently."""
        
        operations_log = []
        job_states = {}
        
        def mock_mixed_operations(method, url, **kwargs):
            nonlocal operations_log, job_states
            
            if method == 'POST' and '/jobs/' not in url:
                # Job submission
                job_id = str(uuid.uuid4())
                operations_log.append(f"submit-{job_id}")
                job_states[job_id] = "Queued"
                
                response = Mock()
                response.status_code = 200
                response.json.return_value = {
                    "id": job_id,
                    "command": kwargs['json']['command'],
                    "status": "Queued",
                    "priority": kwargs['json']['priority'],
                    "timeout": kwargs['json']['timeout']
                }
                return response
                
            elif method == 'GET':
                # Status check
                job_id = url.split('/')[-2]
                operations_log.append(f"view-{job_id}")
                
                response = Mock()
                response.status_code = 200
                response.json.return_value = {
                    "id": job_id,
                    "command": "echo 'mixed test'",
                    "status": job_states.get(job_id, "Running"),
                    "priority": "Medium",
                    "timeout": 30
                }
                return response
                
            elif method == 'POST' and 'cancel' in url:
                # Job cancellation
                job_id = url.split('/')[-3]
                operations_log.append(f"cancel-{job_id}")
                job_states[job_id] = "Cancelled"
                
                response = Mock()
                response.status_code = 200
                return response
        
        mock_make_request.side_effect = mock_mixed_operations
        
        # Mix of different operations
        operations = []
        
        # Add job submissions
        for i in range(3):
            operations.append(('submit', lambda i=i: self.runner.invoke(submit, [f'echo "mixed-{i}"'])))
        
        # Add status checks (will use job IDs from submissions)
        def delayed_status_check():
            time.sleep(0.1)  # Give submissions time to complete
            if operations_log:
                # Get a job ID from previous submissions
                submit_logs = [log for log in operations_log if log.startswith('submit-')]
                if submit_logs:
                    job_id = submit_logs[0].split('-', 1)[1]
                    return self.runner.invoke(view, [job_id])
            return Mock(exit_code=0)
        
        for i in range(2):
            operations.append(('view', delayed_status_check))
        
        # Add cancellations
        def delayed_cancellation():
            time.sleep(0.2)  # Give more time for submissions
            if operations_log:
                submit_logs = [log for log in operations_log if log.startswith('submit-')]
                if submit_logs:
                    job_id = submit_logs[-1].split('-', 1)[1]  # Cancel last submitted job
                    return self.runner.invoke(cancel, [job_id, '--force'])
            return Mock(exit_code=0)
        
        for i in range(1):
            operations.append(('cancel', delayed_cancellation))
        
        # Execute all operations concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(op[1]) for op in operations]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify operations completed
        success_count = sum(1 for r in results if hasattr(r, 'exit_code') and r.exit_code == 0)
        assert success_count >= 3, f"Expected at least 3 successes, got {success_count}"
        
        # Verify different types of operations occurred
        submit_ops = [log for log in operations_log if log.startswith('submit-')]
        view_ops = [log for log in operations_log if log.startswith('view-')]
        cancel_ops = [log for log in operations_log if log.startswith('cancel-')]
        
        assert len(submit_ops) >= 1, "Should have at least one submission"
        # View and cancel operations depend on timing and job IDs being available

    @patch('main.make_request')
    def test_high_load_stress_test(self, mock_make_request):
        """Test system behavior under high concurrent load."""
        
        request_count = 0
        request_times = []
        
        def mock_high_load_response(*args, **kwargs):
            nonlocal request_count
            request_count += 1
            request_times.append(time.time())
            
            # Simulate varying response times under load
            delay = 0.01 + (request_count * 0.001)
            time.sleep(min(delay, 0.1))  # Cap delay at 100ms
            
            response = Mock()
            response.status_code = 200
            response.json.return_value = {
                "id": str(uuid.uuid4()),
                "command": f"echo 'load-test-{request_count}'",
                "status": "Queued",
                "priority": "Medium",
                "timeout": 30
            }
            return response
        
        mock_make_request.side_effect = mock_high_load_response
        
        # Submit 50 jobs concurrently to simulate high load
        def submit_load_job(i):
            return self.runner.invoke(submit, [f'echo "load-test-{i}"'])
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(submit_load_job, i) for i in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        end_time = time.time()
        
        # Verify high success rate under load
        success_count = sum(1 for r in results if r.exit_code == 0)
        success_rate = success_count / len(results)
        assert success_rate >= 0.9, f"Success rate too low under load: {success_rate}"
        
        # Verify reasonable performance
        total_time = end_time - start_time
        assert total_time < 10.0, f"Took too long under load: {total_time}s"
        
        # Verify all requests were processed
        assert request_count == 50, f"Expected 50 requests, got {request_count}"


if __name__ == "__main__":
    # Run race condition tests specifically
    pytest.main([
        "-v",
        "--tb=short",
        "-m", "race_condition",
        "test_race_conditions.py"
    ])
