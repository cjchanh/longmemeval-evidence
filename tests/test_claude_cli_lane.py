"""Unit tests for scripts/claude_cli_lane.py.

All subprocess calls are mocked — no live `claude` invocations here (those
live in eval/dense_chain_v32_20260830/v4/claude_lane/SMOKE.md as a separate,
explicitly-bounded 3-call live smoke test). The `shutil.which` binary lookup
is mocked too, so the suite is hermetic on machines without the `claude`
binary installed; the one test that exercises the not-found branch re-patches
`which` to return None locally.
"""
from __future__ import annotations

import subprocess
import unittest
from unittest import mock

from scripts.claude_cli_lane import (
    ClaudeCliLaneError,
    _ARGV_PROMPT_MAX_CHARS,
    _CHROME,
    _LANE_DOWN,
    claude_cli_generate,
    effective_timeout_s,
)


def _proc(returncode=0, stdout=b"", stderr=b""):
    return subprocess.CompletedProcess(
        args=["claude"], returncode=returncode, stdout=stdout, stderr=stderr
    )


class TestEffectiveTimeout(unittest.TestCase):
    def test_explicit_timeout_wins(self):
        self.assertEqual(effective_timeout_s("x" * 999999, 42), 42)

    def test_floor_on_short_prompt(self):
        self.assertEqual(effective_timeout_s("hi", None), 300)

    def test_scales_with_length(self):
        # 240 + 200000//400 = 240 + 500 = 740
        self.assertEqual(effective_timeout_s("x" * 200000, None), 740)

    def test_cap_on_long_prompt(self):
        self.assertEqual(effective_timeout_s("x" * 10_000_000, None), 900)


class TestBannerRegex(unittest.TestCase):
    def test_unrecognized_model_tag_matches(self):
        self.assertTrue(_LANE_DOWN.search(
            '[claude-code:unrecognized_model] {"model":"bogus"}'))

    def test_rate_limit_matches(self):
        self.assertTrue(_LANE_DOWN.search("You have hit the rate limit"))

    def test_quota_matches(self):
        self.assertTrue(_LANE_DOWN.search("quota exceeded for this account"))

    def test_login_required_matches(self):
        self.assertTrue(_LANE_DOWN.search("log in required to continue"))

    def test_leading_error_colon_matches(self):
        self.assertTrue(_LANE_DOWN.match("error: unknown option '--bogus'"))

    def test_ordinary_answer_does_not_match(self):
        # An answer that later mentions "quota" is fine — only a
        # start-anchored match against stdout counts (see claude_cli_generate).
        self.assertIsNone(_LANE_DOWN.match(
            "The character mentioned a data quota in the story."))


class TestChromeGuard(unittest.TestCase):
    def test_trust_dialog_notice_flagged(self):
        self.assertTrue(_CHROME.match(
            "Ignoring 56 permissions.allow entries from .claude/settings.json"))

    def test_permission_rule_notice_flagged(self):
        self.assertTrue(_CHROME.match(
            "Permission deny rule (.claude/settings.json): Write(.env)"))

    def test_real_answer_not_flagged(self):
        self.assertIsNone(_CHROME.match("30 days. 31 days is also acceptable."))


class TestClaudeCliGenerate(unittest.TestCase):
    def setUp(self):
        # Hermetic binary lookup: `_resolve_claude_binary` calls
        # shutil.which("claude") before any (already-mocked) subprocess
        # call, so without this the suite fails on machines without the
        # `claude` binary installed. The returned path is never executed.
        which = mock.patch("scripts.claude_cli_lane.shutil.which",
                           return_value="/usr/bin/claude")
        which.start()
        self.addCleanup(which.stop)

    def test_happy_path_returns_stdout(self):
        with mock.patch("scripts.claude_cli_lane.subprocess.run",
                         return_value=_proc(0, b"PONG\n")) as run:
            out = claude_cli_generate("ping")
        self.assertEqual(out, "PONG")
        run.assert_called_once()

    def test_argv_used_under_threshold(self):
        prompt = "x" * 100
        with mock.patch("scripts.claude_cli_lane.subprocess.run",
                         return_value=_proc(0, b"ok\n")) as run:
            claude_cli_generate(prompt)
        cmd = run.call_args.args[0]
        self.assertIn(prompt, cmd)
        self.assertIsNone(run.call_args.kwargs.get("input"))

    def test_stdin_used_over_argv_threshold(self):
        prompt = "x" * (_ARGV_PROMPT_MAX_CHARS + 1)
        with mock.patch("scripts.claude_cli_lane.subprocess.run",
                         return_value=_proc(0, b"ok\n")) as run:
            claude_cli_generate(prompt)
        cmd = run.call_args.args[0]
        self.assertNotIn(prompt, cmd)
        self.assertEqual(run.call_args.kwargs.get("input"),
                          prompt.encode("utf-8"))

    def test_tools_disabled_and_output_format_text(self):
        with mock.patch("scripts.claude_cli_lane.subprocess.run",
                         return_value=_proc(0, b"ok\n")) as run:
            claude_cli_generate("ping")
        cmd = run.call_args.args[0]
        self.assertIn("--tools", cmd)
        self.assertEqual(cmd[cmd.index("--tools") + 1], "")
        self.assertIn("--output-format", cmd)
        self.assertEqual(cmd[cmd.index("--output-format") + 1], "text")

    def test_model_override_passed_through(self):
        with mock.patch("scripts.claude_cli_lane.subprocess.run",
                         return_value=_proc(0, b"ok\n")) as run:
            claude_cli_generate("ping", model="sonnet")
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")

    def test_empty_prompt_refused_without_subprocess_call(self):
        with mock.patch("scripts.claude_cli_lane.subprocess.run") as run:
            with self.assertRaises(ClaudeCliLaneError):
                claude_cli_generate("")
        run.assert_not_called()

    def test_unrecognized_model_raises_immediately_no_retry(self):
        proc = _proc(
            1, b"There's an issue with the selected model (bogus).\n",
            b'[claude-code:unrecognized_model] {"model":"bogus"}\n')
        with mock.patch("scripts.claude_cli_lane.subprocess.run",
                         return_value=proc) as run:
            with self.assertRaises(ClaudeCliLaneError) as ctx:
                claude_cli_generate("ping", model="bogus")
        run.assert_called_once()  # no retry on a lane-down banner
        self.assertIn("unrecognized_model", str(ctx.exception))

    def test_bad_flag_stderr_raises_immediately(self):
        proc = _proc(1, b"", b"error: unknown option '--bogus'\n")
        with mock.patch("scripts.claude_cli_lane.subprocess.run",
                         return_value=proc) as run:
            with self.assertRaises(ClaudeCliLaneError):
                claude_cli_generate("ping")
        run.assert_called_once()

    def test_error_exit_never_returned_as_answer(self):
        # rc != 0 with no LANE_DOWN banner match, distinct text per attempt
        # (so the identical-failure-twice guard doesn't short-circuit): must
        # not return `out`, must retry the full budget then raise — never
        # hand back error-shaped text.
        procs = [
            _proc(2, f"unexpected failure text {i}\n".encode(), b"")
            for i in range(3)
        ]
        with mock.patch("scripts.claude_cli_lane.subprocess.run",
                         side_effect=procs) as run:
            with self.assertRaises(ClaudeCliLaneError):
                claude_cli_generate("ping", backoff_s=0)
        self.assertEqual(run.call_count, 3)

    def test_repeated_timeout_stops_early(self):
        # The effective timeout is computed once per call (fixed by prompt
        # length/timeout_s), so a repeated TimeoutExpired is by construction
        # an identical failure signature — stop after 2 attempts, not 3.
        with mock.patch(
            "scripts.claude_cli_lane.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=300),
        ) as run:
            with self.assertRaises(ClaudeCliLaneError) as ctx:
                claude_cli_generate("ping", timeout_s=300, backoff_s=0)
        self.assertEqual(run.call_count, 2)
        self.assertIn("timeout", str(ctx.exception))

    def test_identical_failure_twice_stops_early(self):
        # Same rc/out/err signature twice in a row should stop before
        # burning the third attempt.
        proc = _proc(2, b"same failure every time\n", b"")
        with mock.patch("scripts.claude_cli_lane.subprocess.run",
                         return_value=proc) as run:
            with self.assertRaises(ClaudeCliLaneError):
                claude_cli_generate("ping", backoff_s=0, max_attempts=3)
        self.assertEqual(run.call_count, 2)

    def test_chrome_only_stdout_not_returned(self):
        proc = _proc(0, b"Ignoring 56 permissions.allow entries\n", b"")
        with mock.patch("scripts.claude_cli_lane.subprocess.run",
                         return_value=proc) as run:
            with self.assertRaises(ClaudeCliLaneError):
                claude_cli_generate("ping", backoff_s=0, max_attempts=1)
        run.assert_called_once()

    def test_scratch_cwd_used_not_repo_cwd(self):
        with mock.patch("scripts.claude_cli_lane.subprocess.run",
                         return_value=_proc(0, b"ok\n")) as run:
            claude_cli_generate("ping")
        cwd = run.call_args.kwargs.get("cwd")
        self.assertIsNotNone(cwd)
        self.assertIn("lme_claude_cli_lane", cwd)

    def test_missing_binary_raises_without_subprocess_call(self):
        with mock.patch("scripts.claude_cli_lane.shutil.which",
                         return_value=None):
            with mock.patch("scripts.claude_cli_lane.subprocess.run") as run:
                with self.assertRaises(ClaudeCliLaneError):
                    claude_cli_generate("ping")
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
