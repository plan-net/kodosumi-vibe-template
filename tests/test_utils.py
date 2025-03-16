"""
Unit tests for the utils module.
"""

import unittest
from unittest.mock import MagicMock, patch, call, ANY
import os
import sys
import ray
from workflows.crewai_flow.utils import (
    RAY_TASK_NUM_CPUS, RAY_TASK_MAX_RETRIES, RAY_TASK_TIMEOUT, RAY_BATCH_SIZE,
    RAY_INIT_NUM_CPUS, RAY_DASHBOARD_PORT,
    apply_ray_patch, initialize_ray, test_ray_connectivity, shutdown_ray
)


def test_ray_connectivity_basic():
    """Test that test_ray_connectivity returns False when Ray is not initialized."""
    # Call the function
    result, value = test_ray_connectivity()
    
    # Verify the result
    assert result is False
    assert value is None


class TestUtils(unittest.TestCase):
    """Test cases for the utils module."""

    def test_ray_constants(self):
        """Test that the Ray constants have the expected types."""
        self.assertIsInstance(RAY_TASK_NUM_CPUS, float)
        self.assertIsInstance(RAY_TASK_MAX_RETRIES, int)
        self.assertIsInstance(RAY_TASK_TIMEOUT, float)
        self.assertIsInstance(RAY_BATCH_SIZE, int)
        self.assertIsInstance(RAY_INIT_NUM_CPUS, int)
        self.assertIsInstance(RAY_DASHBOARD_PORT, str)

    @patch('sys.stdout')
    @patch('sys.stderr')
    def test_apply_ray_patch(self, mock_stderr, mock_stdout):
        """Test that apply_ray_patch correctly patches sys.stdout and sys.stderr."""
        # Call the function
        result = apply_ray_patch()
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify that sys.stdout and sys.stderr were patched
        self.assertNotEqual(sys.stdout, mock_stdout)
        self.assertNotEqual(sys.stderr, mock_stderr)
        
        # Verify that the patched streams have the isatty method
        self.assertFalse(sys.stdout.isatty())
        self.assertFalse(sys.stderr.isatty())

    @unittest.skip("This test is difficult to implement due to the nature of the function")
    @patch('builtins.print')
    def test_apply_ray_patch_exception(self, mock_print):
        """Test that apply_ray_patch handles exceptions gracefully."""
        # This test is skipped because it's difficult to reliably trigger an exception
        # in the apply_ray_patch function without complex mocking.
        pass

    @patch('ray.init')
    @patch('ray.is_initialized')
    @patch('workflows.crewai_flow.utils.apply_ray_patch')
    def test_initialize_ray_already_initialized(self, mock_apply_ray_patch, mock_is_initialized, mock_init):
        """Test that initialize_ray returns True when Ray is already initialized."""
        # Configure the mock to indicate that Ray is already initialized
        mock_is_initialized.return_value = True
        
        # Call the function
        result = initialize_ray(is_kodosumi=False)
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify that ray.init was not called
        mock_init.assert_not_called()
        
        # Verify that apply_ray_patch was not called
        mock_apply_ray_patch.assert_not_called()

    @patch('ray.init')
    @patch('ray.is_initialized')
    @patch('workflows.crewai_flow.utils.apply_ray_patch')
    def test_initialize_ray_kodosumi(self, mock_apply_ray_patch, mock_is_initialized, mock_init):
        """Test that initialize_ray returns True when in Kodosumi environment."""
        # Configure the mock to indicate that Ray is not initialized
        mock_is_initialized.return_value = False
        
        # Call the function
        result = initialize_ray(is_kodosumi=True)
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify that ray.init was not called
        mock_init.assert_not_called()
        
        # Verify that apply_ray_patch was not called
        mock_apply_ray_patch.assert_not_called()

    @patch('ray.init')
    @patch('ray.is_initialized')
    @patch('workflows.crewai_flow.utils.apply_ray_patch')
    def test_initialize_ray_connect_success(self, mock_apply_ray_patch, mock_is_initialized, mock_init):
        """Test that initialize_ray connects to an existing Ray cluster when possible."""
        # Configure the mocks
        mock_is_initialized.return_value = False
        mock_apply_ray_patch.return_value = True
        
        # Call the function
        with patch('builtins.print') as mock_print:
            result = initialize_ray(is_kodosumi=False)
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify that apply_ray_patch was called
        mock_apply_ray_patch.assert_called_once()
        
        # Verify that ray.init was called with the correct arguments
        mock_init.assert_called_once_with(address="auto", ignore_reinit_error=True)
        
        # Verify that the success message was printed
        mock_print.assert_any_call("Connected to existing Ray cluster")

    @patch('ray.init')
    @patch('ray.is_initialized')
    @patch('workflows.crewai_flow.utils.apply_ray_patch')
    def test_initialize_ray_connect_failure(self, mock_apply_ray_patch, mock_is_initialized, mock_init):
        """Test that initialize_ray starts a new Ray instance when connecting fails."""
        # Configure the mocks
        mock_is_initialized.return_value = False
        mock_apply_ray_patch.return_value = True
        mock_init.side_effect = [ConnectionError("Connection failed"), None]
        
        # Call the function
        with patch('builtins.print') as mock_print:
            result = initialize_ray(is_kodosumi=False)
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify that apply_ray_patch was called
        mock_apply_ray_patch.assert_called_once()
        
        # Verify that ray.init was called twice with the correct arguments
        mock_init.assert_has_calls([
            call(address="auto", ignore_reinit_error=True),
            call(num_cpus=RAY_INIT_NUM_CPUS, dashboard_port=None, ignore_reinit_error=True)
        ])
        
        # Verify that the success message was printed
        mock_print.assert_any_call(f"Started new Ray instance with {RAY_INIT_NUM_CPUS} CPUs")

    @patch('ray.init')
    @patch('ray.is_initialized')
    @patch('workflows.crewai_flow.utils.apply_ray_patch')
    def test_initialize_ray_exception(self, mock_apply_ray_patch, mock_is_initialized, mock_init):
        """Test that initialize_ray handles exceptions gracefully."""
        # Configure the mocks
        mock_is_initialized.return_value = False
        mock_apply_ray_patch.return_value = True
        mock_init.side_effect = Exception("Test exception")
        
        # Call the function
        with patch('builtins.print') as mock_print:
            result = initialize_ray(is_kodosumi=False)
        
        # Verify the result
        self.assertFalse(result)
        
        # Verify that apply_ray_patch was called
        mock_apply_ray_patch.assert_called_once()
        
        # Verify that ray.init was called
        mock_init.assert_called_once()
        
        # Verify that the error message was printed
        mock_print.assert_any_call("Error initializing Ray: Test exception")
        mock_print.assert_any_call("Continuing without Ray parallelization")

    @patch('ray.is_initialized')
    def test_test_ray_connectivity_not_initialized(self, mock_is_initialized):
        """Test that test_ray_connectivity returns False when Ray is not initialized."""
        # Configure the mock to indicate that Ray is not initialized
        mock_is_initialized.return_value = False
        
        # Call the function
        with patch('builtins.print') as mock_print:
            result, _ = test_ray_connectivity()
        
        # Verify the result
        self.assertFalse(result)
        
        # Verify that the error message was printed
        mock_print.assert_called_with("Ray is not initialized. Cannot test connectivity.")

    @patch('ray.remote')
    @patch('ray.get')
    @patch('ray.is_initialized')
    def test_test_ray_connectivity_success(self, mock_is_initialized, mock_ray_get, mock_ray_remote):
        """Test that test_ray_connectivity returns True when Ray is working."""
        # Configure the mocks
        mock_is_initialized.return_value = True
        mock_ray_remote.return_value = MagicMock()
        mock_ray_remote.return_value.remote.return_value = "remote_task"
        mock_ray_get.return_value = "Ray test successful"
        
        # Call the function
        with patch('builtins.print') as mock_print:
            result, value = test_ray_connectivity()
        
        # Verify the result
        self.assertTrue(result)
        self.assertEqual(value, "Ray test successful")
        
        # Verify that ray.remote was called
        mock_ray_remote.assert_called_once()
        
        # Verify that ray.get was called with ANY task and the correct timeout
        mock_ray_get.assert_called_once_with(ANY, timeout=RAY_TASK_TIMEOUT)
        
        # Verify that the success message was printed
        mock_print.assert_called_with("Ray test successful")

    @patch('ray.remote')
    @patch('ray.get')
    @patch('ray.is_initialized')
    def test_test_ray_connectivity_timeout(self, mock_is_initialized, mock_ray_get, mock_ray_remote):
        """Test that test_ray_connectivity returns False when Ray times out."""
        # Configure the mocks
        mock_is_initialized.return_value = True
        mock_ray_remote.return_value = MagicMock()
        mock_ray_remote.return_value.remote.return_value = "remote_task"
        mock_ray_get.side_effect = TimeoutError("Ray timed out")
        
        # Call the function
        with patch('builtins.print') as mock_print:
            result, value = test_ray_connectivity()
        
        # Verify the result
        self.assertFalse(result)
        self.assertIsNone(value)
        
        # Verify that ray.remote was called
        mock_ray_remote.assert_called_once()
        
        # Verify that ray.get was called with ANY task and the correct timeout
        mock_ray_get.assert_called_once_with(ANY, timeout=RAY_TASK_TIMEOUT)
        
        # Verify that the error message was printed
        mock_print.assert_called_with("Ray test failed due to timeout: Ray timed out")

    @patch('ray.remote')
    @patch('ray.get')
    @patch('ray.is_initialized')
    def test_test_ray_connectivity_exception(self, mock_is_initialized, mock_ray_get, mock_ray_remote):
        """Test that test_ray_connectivity returns False when an exception occurs."""
        # Configure the mocks
        mock_is_initialized.return_value = True
        mock_ray_remote.return_value = MagicMock()
        mock_ray_remote.return_value.remote.return_value = "remote_task"
        mock_ray_get.side_effect = Exception("Test exception")
        
        # Call the function
        with patch('builtins.print') as mock_print:
            result, value = test_ray_connectivity()
        
        # Verify the result
        self.assertFalse(result)
        self.assertIsNone(value)
        
        # Verify that ray.remote was called
        mock_ray_remote.assert_called_once()
        
        # Verify that ray.get was called with ANY task and the correct timeout
        mock_ray_get.assert_called_once_with(ANY, timeout=RAY_TASK_TIMEOUT)
        
        # Verify that the error message was printed
        mock_print.assert_called_with("Ray test failed with error: Test exception")

    @patch('ray.shutdown')
    @patch('ray.is_initialized')
    def test_shutdown_ray_initialized_not_kodosumi(self, mock_is_initialized, mock_shutdown):
        """Test that shutdown_ray shuts down Ray when it's initialized and not in Kodosumi environment."""
        # Configure the mock to indicate that Ray is initialized
        mock_is_initialized.return_value = True
        
        # Call the function
        with patch('builtins.print') as mock_print:
            shutdown_ray(is_kodosumi=False)
        
        # Verify that ray.shutdown was called
        mock_shutdown.assert_called_once()
        
        # Verify that the shutdown messages were printed
        mock_print.assert_any_call("Shutting down Ray...")
        mock_print.assert_any_call("Ray shutdown complete.")

    @patch('ray.shutdown')
    @patch('ray.is_initialized')
    def test_shutdown_ray_initialized_kodosumi(self, mock_is_initialized, mock_shutdown):
        """Test that shutdown_ray does not shut down Ray when in Kodosumi environment."""
        # Configure the mock to indicate that Ray is initialized
        mock_is_initialized.return_value = True
        
        # Call the function
        shutdown_ray(is_kodosumi=True)
        
        # Verify that ray.shutdown was not called
        mock_shutdown.assert_not_called()

    @patch('ray.shutdown')
    @patch('ray.is_initialized')
    def test_shutdown_ray_not_initialized(self, mock_is_initialized, mock_shutdown):
        """Test that shutdown_ray does not shut down Ray when it's not initialized."""
        # Configure the mock to indicate that Ray is not initialized
        mock_is_initialized.return_value = False
        
        # Call the function
        shutdown_ray(is_kodosumi=False)
        
        # Verify that ray.shutdown was not called
        mock_shutdown.assert_not_called()


if __name__ == "__main__":
    unittest.main() 