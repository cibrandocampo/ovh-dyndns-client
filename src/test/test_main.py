"""Tests for `main.launch_scheduler`.

The rest of `main.main()` is the application entrypoint and is not
unit-tested (it boots the DB, runs migrations, starts uvicorn). The
scheduler-launch helper is the one piece carrying real branching logic
(env-var-driven enable/disable), so we test it in isolation.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# `main.py` lives at <project>/src/main.py. Test runs cwd-agnostic by
# putting `src/` on sys.path before importing.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main as main_module  # noqa: E402


class TestLaunchScheduler(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("DISABLE_SCHEDULER", None)

    @patch("main.SchedulerThread")
    def test_disable_scheduler_env_skips_start(self, mock_thread_cls):
        """`DISABLE_SCHEDULER=1` returns None and does not instantiate the thread."""
        os.environ["DISABLE_SCHEDULER"] = "1"
        result = main_module.launch_scheduler(MagicMock(), MagicMock())
        self.assertIsNone(result)
        mock_thread_cls.assert_not_called()

    @patch("main.SchedulerThread")
    def test_default_starts_scheduler(self, mock_thread_cls):
        """Without the env var, a thread is created and started."""
        os.environ.pop("DISABLE_SCHEDULER", None)
        instance = mock_thread_cls.return_value

        controller = MagicMock()
        repository = MagicMock()
        result = main_module.launch_scheduler(controller, repository)

        mock_thread_cls.assert_called_once_with(controller, repository)
        instance.start.assert_called_once()
        self.assertIs(result, instance)

    @patch("main.SchedulerThread")
    def test_other_truthy_values_do_not_disable(self, mock_thread_cls):
        """Only the literal `'1'` disables; other strings still launch the thread."""
        os.environ["DISABLE_SCHEDULER"] = "true"  # not '1' — does NOT disable
        instance = mock_thread_cls.return_value
        result = main_module.launch_scheduler(MagicMock(), MagicMock())
        mock_thread_cls.assert_called_once()
        instance.start.assert_called_once()
        self.assertIs(result, instance)


if __name__ == "__main__":
    unittest.main()
