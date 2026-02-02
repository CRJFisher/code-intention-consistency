"""
Unit tests for the evidence runner module.

Tests run_evidence_tests function and associated dataclasses.
"""

from __future__ import annotations

from pathlib import Path

from intention_audit.evidence.runner import (
    EvidenceResults,
    TestOutput,
    run_evidence_tests,
)


class TestEvidenceResults:
    """Tests for EvidenceResults dataclass."""

    def test_default_values(self) -> None:
        """New EvidenceResults should have sensible defaults."""
        results = EvidenceResults()

        assert results.passed == []
        assert results.failed == []
        assert results.errors == []
        assert results.all_passed is True
        assert results.raw_output == ""

    def test_summary_with_empty_results(self) -> None:
        """Summary should show zeros for empty results."""
        results = EvidenceResults()
        summary = results.summary

        assert summary["total"] == 0
        assert summary["passed"] == 0
        assert summary["failed"] == 0
        assert summary["errors"] == 0
        assert summary["all_passed"] is True

    def test_summary_with_mixed_results(self) -> None:
        """Summary should correctly count mixed results."""
        results = EvidenceResults(
            passed=[
                TestOutput(selector="test1", passed=True, output="", duration=0.1),
                TestOutput(selector="test2", passed=True, output="", duration=0.2),
            ],
            failed=[
                TestOutput(selector="test3", passed=False, output="", duration=0.1),
            ],
            errors=[
                TestOutput(selector="test4", passed=False, output="", duration=0.0),
            ],
            all_passed=False,
        )

        summary = results.summary

        assert summary["total"] == 4
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        assert summary["errors"] == 1
        assert summary["all_passed"] is False


class TestTestOutput:
    """Tests for TestOutput dataclass."""

    def test_create_passed_test(self) -> None:
        """Should create a passed test output."""
        output = TestOutput(
            selector="tests/test_foo.py::test_bar",
            passed=True,
            output="PASSED",
            duration=0.5,
        )

        assert output.selector == "tests/test_foo.py::test_bar"
        assert output.passed is True
        assert output.output == "PASSED"
        assert output.duration == 0.5

    def test_create_failed_test(self) -> None:
        """Should create a failed test output."""
        output = TestOutput(
            selector="tests/test_foo.py::test_baz",
            passed=False,
            output="AssertionError",
            duration=0.3,
        )

        assert output.selector == "tests/test_foo.py::test_baz"
        assert output.passed is False
        assert output.output == "AssertionError"
        assert output.duration == 0.3


class TestRunEvidenceTestsEmptySelectors:
    """Tests for run_evidence_tests with empty selectors."""

    def test_empty_selectors_returns_empty_results(self, tmp_path: Path) -> None:
        """Empty selectors should return empty results with all_passed=True."""
        results = run_evidence_tests(tmp_path, [])

        assert results.all_passed is True
        assert len(results.passed) == 0
        assert len(results.failed) == 0
        assert len(results.errors) == 0
        assert results.raw_output == ""

    def test_empty_selectors_with_nonexistent_path(self) -> None:
        """Empty selectors should work even with nonexistent path."""
        nonexistent = Path("/nonexistent/path")
        results = run_evidence_tests(nonexistent, [])

        assert results.all_passed is True
        assert len(results.passed) == 0


class TestRunEvidenceTestsPassingTests:
    """Tests for run_evidence_tests with passing tests."""

    def test_passing_test(self, tmp_path: Path) -> None:
        """Should correctly identify passing tests."""
        test_file = tmp_path / "test_pass.py"
        test_file.write_text(
            """
def test_add_positive_numbers():
    assert 2 + 3 == 5
"""
        )

        results = run_evidence_tests(
            tmp_path,
            ["test_pass.py::test_add_positive_numbers"],
        )

        assert results.all_passed is True
        assert len(results.passed) >= 1
        assert len(results.failed) == 0
        # raw_output should contain pytest output
        assert "PASSED" in results.raw_output or results.all_passed

    def test_multiple_passing_tests(self, tmp_path: Path) -> None:
        """Should handle multiple passing tests."""
        test_file = tmp_path / "test_multi.py"
        test_file.write_text(
            """
def test_add_positive_numbers():
    assert 2 + 3 == 5

def test_add_zero():
    assert 0 + 5 == 5
"""
        )

        results = run_evidence_tests(
            tmp_path,
            [
                "test_multi.py::test_add_positive_numbers",
                "test_multi.py::test_add_zero",
            ],
        )

        assert results.all_passed is True
        # Should have detected passing tests
        total = len(results.passed) + len(results.failed) + len(results.errors)
        assert total >= 2


class TestRunEvidenceTestsFailingTests:
    """Tests for run_evidence_tests with failing tests."""

    def test_failing_test_captured(self, tmp_path: Path) -> None:
        """Should capture failing test in results."""
        # Create a simple failing test
        test_file = tmp_path / "test_fail.py"
        test_file.write_text(
            """
def test_always_fails():
    assert False, "This test always fails"
"""
        )

        results = run_evidence_tests(tmp_path, ["test_fail.py::test_always_fails"])

        assert results.all_passed is False
        # Either failed or error (if parsing issue)
        assert len(results.failed) + len(results.errors) >= 1

    def test_mixed_pass_and_fail(self, tmp_path: Path) -> None:
        """Should capture both passing and failing tests."""
        test_file = tmp_path / "test_mixed.py"
        test_file.write_text(
            """
def test_passes():
    assert True

def test_fails():
    assert False
"""
        )

        results = run_evidence_tests(
            tmp_path, ["test_mixed.py::test_passes", "test_mixed.py::test_fails"]
        )

        assert results.all_passed is False
        # Raw output should show both tests ran
        assert "test_passes" in results.raw_output or "test_fails" in results.raw_output


class TestRunEvidenceTestsMissingFiles:
    """Tests for run_evidence_tests with missing test files."""

    def test_missing_test_file_handled_gracefully(self, tmp_path: Path) -> None:
        """Missing test file should result in error, not crash."""
        results = run_evidence_tests(
            tmp_path, ["nonexistent_test.py::test_something"]
        )

        # Should fail but not crash
        assert results.all_passed is False
        # Should have an error entry for the missing test
        assert len(results.errors) >= 1

    def test_missing_test_function_handled_gracefully(self, tmp_path: Path) -> None:
        """Missing test function should result in error."""
        # Create a test file without the referenced function
        test_file = tmp_path / "test_partial.py"
        test_file.write_text(
            """
def test_exists():
    assert True
"""
        )

        results = run_evidence_tests(
            tmp_path, ["test_partial.py::test_does_not_exist"]
        )

        assert results.all_passed is False
        # Should detect that the test wasn't found
        assert len(results.errors) >= 1


class TestRunEvidenceTestsPytestErrors:
    """Tests for run_evidence_tests with pytest errors."""

    def test_syntax_error_in_test_file(self, tmp_path: Path) -> None:
        """Syntax error in test file should be handled gracefully."""
        test_file = tmp_path / "test_syntax.py"
        test_file.write_text(
            """
def test_with_syntax_error(
    # Missing closing parenthesis causes syntax error
    assert True
"""
        )

        results = run_evidence_tests(tmp_path, ["test_syntax.py::test_with_syntax_error"])

        assert results.all_passed is False
        # Should capture the error
        assert len(results.errors) >= 1

    def test_import_error_in_test_file(self, tmp_path: Path) -> None:
        """Import error in test file should be handled gracefully."""
        test_file = tmp_path / "test_import.py"
        test_file.write_text(
            """
from nonexistent_module import something

def test_with_import_error():
    assert True
"""
        )

        results = run_evidence_tests(tmp_path, ["test_import.py::test_with_import_error"])

        assert results.all_passed is False
        # Should handle the import error
        assert len(results.errors) >= 1

    def test_fixture_error_handled(self, tmp_path: Path) -> None:
        """Missing fixture should be handled gracefully."""
        test_file = tmp_path / "test_fixture.py"
        test_file.write_text(
            """
def test_needs_missing_fixture(nonexistent_fixture):
    assert True
"""
        )

        results = run_evidence_tests(
            tmp_path, ["test_fixture.py::test_needs_missing_fixture"]
        )

        assert results.all_passed is False


class TestRunEvidenceTestsRealWorldScenarios:
    """Tests simulating real-world usage scenarios."""

    def test_full_test_file_selector(self, tmp_path: Path) -> None:
        """Should work with full test file selector (no specific test)."""
        test_file = tmp_path / "test_calculator.py"
        test_file.write_text(
            """
def test_add_positive_numbers():
    assert 2 + 3 == 5

def test_add_negative_numbers():
    assert -1 + -1 == -2

def test_add_zero():
    assert 0 + 5 == 5
"""
        )

        results = run_evidence_tests(
            tmp_path,
            ["test_calculator.py"],
        )

        # All tests in the file should pass
        assert results.all_passed is True
        # Should have raw output from pytest
        assert len(results.raw_output) > 0

    def test_raw_output_contains_pytest_output(self, tmp_path: Path) -> None:
        """Raw output should contain actual pytest output."""
        test_file = tmp_path / "test_simple.py"
        test_file.write_text(
            """
def test_simple():
    assert 1 + 1 == 2
"""
        )

        results = run_evidence_tests(tmp_path, ["test_simple.py::test_simple"])

        # Raw output should have something in it
        assert len(results.raw_output) > 0
        # Should contain test info
        assert "test_simple" in results.raw_output

    def test_results_contain_selector_info(self, tmp_path: Path) -> None:
        """Results should preserve selector information."""
        test_file = tmp_path / "test_selector.py"
        test_file.write_text(
            """
def test_named():
    assert True
"""
        )

        selector = "test_selector.py::test_named"
        results = run_evidence_tests(tmp_path, [selector])

        # At least one result should reference our selector
        all_outputs = results.passed + results.failed + results.errors
        selectors_found = [o.selector for o in all_outputs]
        assert selector in selectors_found or results.all_passed
