"""Tests for `main.launch_scheduler`.

The rest of `main.main()` is the application entrypoint and is not
unit-tested (it boots the DB, runs migrations, starts uvicorn). The
scheduler-launch helper is the one piece carrying real branching logic
(env-var-driven enable/disable), so we test it in isolation.
"""

import os
import sys
import threading
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


class _CountingController:
    """Controller double that records calls and can raise on chosen calls."""

    def __init__(self, fail_on=()):
        self.calls = 0
        self.fail_on = set(fail_on)
        self.called = threading.Condition()

    def handler(self):
        with self.called:
            self.calls += 1
            self.called.notify_all()
        if self.calls in self.fail_on:
            raise ValueError(f"boom on call {self.calls}")

    def wait_for_calls(self, n, timeout=3):
        with self.called:
            return self.called.wait_for(lambda: self.calls >= n, timeout=timeout)


class TestSchedulerThread(unittest.TestCase):
    def _start(self, controller, repository):
        scheduler = main_module.SchedulerThread(controller, repository)
        scheduler.start()
        self.addCleanup(scheduler.join, 3)
        self.addCleanup(scheduler.stop)
        return scheduler

    def test_survives_non_runtime_controller_errors(self):
        controller = _CountingController(fail_on={1})
        repository = MagicMock()
        repository.get_settings.return_value = {"update_interval": 0.01}

        scheduler = self._start(controller, repository)

        self.assertTrue(controller.wait_for_calls(2), "scheduler stopped after a ValueError")
        self.assertTrue(scheduler.is_alive())

    def test_survives_settings_read_errors(self):
        controller = _CountingController()
        repository = MagicMock()
        calls = {"n": 0}

        def get_settings():
            calls["n"] += 1
            if calls["n"] == 2:
                raise OSError("database is locked")
            return {"update_interval": 0.01}

        repository.get_settings.side_effect = get_settings

        scheduler = self._start(controller, repository)

        self.assertTrue(controller.wait_for_calls(3), "scheduler stopped after a settings read error")
        self.assertTrue(scheduler.is_alive())

    def test_wake_applies_shorter_interval_immediately(self):
        controller = _CountingController()
        repository = MagicMock()
        repository.get_settings.return_value = {"update_interval": 3600}

        scheduler = self._start(controller, repository)
        self.assertTrue(controller.wait_for_calls(1))

        repository.get_settings.return_value = {"update_interval": 0.01}
        scheduler.wake()

        self.assertTrue(controller.wait_for_calls(2), "new interval waited for the old 3600 s one")

    def test_wake_with_longer_interval_does_not_run_early(self):
        controller = _CountingController()
        repository = MagicMock()
        repository.get_settings.return_value = {"update_interval": 3600}

        scheduler = self._start(controller, repository)
        self.assertTrue(controller.wait_for_calls(1))

        repository.get_settings.return_value = {"update_interval": 7200}
        scheduler.wake()

        self.assertFalse(controller.wait_for_calls(2, timeout=0.5))

    def test_stop_interrupts_the_wait(self):
        controller = _CountingController()
        repository = MagicMock()
        repository.get_settings.return_value = {"update_interval": 3600}

        scheduler = main_module.SchedulerThread(controller, repository)
        scheduler.start()
        self.assertTrue(controller.wait_for_calls(1))

        scheduler.stop()
        scheduler.join(timeout=2)

        self.assertFalse(scheduler.is_alive())


class TestOnSettingsChange(unittest.TestCase):
    def test_wakes_the_scheduler(self):
        scheduler = MagicMock()
        main_module.on_settings_change({"update_interval": 60}, scheduler=scheduler)
        scheduler.wake.assert_called_once()

    def test_without_scheduler_is_a_noop(self):
        main_module.on_settings_change({"update_interval": 60}, scheduler=None)


if __name__ == "__main__":
    unittest.main()
