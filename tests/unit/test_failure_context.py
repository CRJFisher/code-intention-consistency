"""Unit tests for intention failure context builder."""

import pytest

from intention_audit.models.evidence_results import EvidenceResult, EvidenceResults
from intention_audit.models.intention import Intention, IntentionKind, IntentionStatus
from intention_audit.reporting.failure_context import (
    IntentionFailureContext,
    build_failure_context,
)


@pytest.fixture
def sample_tree_with_evidence() -> Intention:
    """Create a sample intention tree with evidence_tests for testing."""
    tests_node = Intention(
        id="INT-2026-01-30-0005",
        title="Auth Tests",
        kind=IntentionKind.TESTS,
        status=IntentionStatus.IMPLEMENTED,
        evidence_tests=[
            "tests/test_auth.py::test_login",
            "tests/test_auth.py::test_logout",
        ],
        supporting_docs=["docs/auth.md#login"],
    )
    implementation = Intention(
        id="INT-2026-01-30-0003",
        title="Add Feature",
        kind=IntentionKind.IMPLEMENTATION,
        status=IntentionStatus.IMPLEMENTED,
        evidence_tests=["tests/test_feature.py::test_add"],
        supporting_docs=["docs/feature.md"],
    )
    functionality = Intention(
        id="INT-2026-01-30-0002",
        title="User Authentication",
        kind=IntentionKind.FUNCTIONALITY,
        status=IntentionStatus.IN_PROGRESS,
        code_home=["src/auth/"],
        children=[implementation, tests_node],
    )
    goal = Intention(
        id="INT-2026-01-30-0001",
        title="Security Goal",
        kind=IntentionKind.GOAL,
        status=IntentionStatus.PLANNED,
        children=[functionality],
    )
    return goal


@pytest.fixture
def multi_functionality_tree() -> Intention:
    """Create a tree with multiple functionalities for cross-intention failure tests."""
    auth_tests = Intention(
        id="INT-2026-01-30-0010",
        title="Auth Tests",
        kind=IntentionKind.TESTS,
        status=IntentionStatus.IMPLEMENTED,
        evidence_tests=["tests/test_auth.py::test_login"],
        supporting_docs=["docs/auth.md"],
    )
    auth_func = Intention(
        id="INT-2026-01-30-0011",
        title="Authentication",
        kind=IntentionKind.FUNCTIONALITY,
        status=IntentionStatus.IMPLEMENTED,
        code_home=["src/auth/"],
        children=[auth_tests],
    )

    payment_tests = Intention(
        id="INT-2026-01-30-0020",
        title="Payment Tests",
        kind=IntentionKind.TESTS,
        status=IntentionStatus.IMPLEMENTED,
        evidence_tests=["tests/test_payment.py::test_process"],
        supporting_docs=["docs/payment.md"],
    )
    payment_func = Intention(
        id="INT-2026-01-30-0021",
        title="Payment Processing",
        kind=IntentionKind.FUNCTIONALITY,
        status=IntentionStatus.IMPLEMENTED,
        code_home=["src/payment/"],
        children=[payment_tests],
    )

    goal = Intention(
        id="INT-2026-01-30-0001",
        title="E-Commerce Goal",
        kind=IntentionKind.GOAL,
        status=IntentionStatus.IN_PROGRESS,
        children=[auth_func, payment_func],
    )
    return goal


class TestBuildFailureContextSingleFailure:
    """Tests for single failure scenario."""

    def test_single_failure_linked_to_one_intention(
        self, sample_tree_with_evidence: Intention
    ) -> None:
        """Test that a single test failure is linked to the correct intention."""
        evidence_results = EvidenceResults(
            results=[
                EvidenceResult(
                    selector="tests/test_feature.py::test_add",
                    passed=False,
                    output="AssertionError: expected 1 got 2",
                    duration=0.5,
                )
            ],
            all_passed=False,
        )

        contexts = build_failure_context(sample_tree_with_evidence, evidence_results)

        assert len(contexts) == 1
        ctx = contexts[0]
        assert ctx.intention_id == "INT-2026-01-30-0003"
        assert ctx.intention_title == "Add Feature"
        assert "tests/test_feature.py::test_add" in ctx.failed_tests
        assert ctx.linked_docs == ["docs/feature.md"]
        assert ctx.code_scope == ["src/auth/"]

    def test_failure_context_has_correct_path(self, sample_tree_with_evidence: Intention) -> None:
        """Test that intention_path is correctly computed."""
        evidence_results = EvidenceResults(
            results=[
                EvidenceResult(
                    selector="tests/test_feature.py::test_add",
                    passed=False,
                )
            ],
            all_passed=False,
        )

        contexts = build_failure_context(sample_tree_with_evidence, evidence_results)

        assert len(contexts) == 1
        assert contexts[0].intention_path == "Security Goal/User Authentication/Add Feature"


class TestBuildFailureContextMultipleFailures:
    """Tests for multiple failures on the same intention."""

    def test_multiple_failures_same_intention(self, sample_tree_with_evidence: Intention) -> None:
        """Test that multiple test failures for same intention are aggregated."""
        evidence_results = EvidenceResults(
            results=[
                EvidenceResult(
                    selector="tests/test_auth.py::test_login",
                    passed=False,
                    output="Login failed",
                    duration=0.3,
                ),
                EvidenceResult(
                    selector="tests/test_auth.py::test_logout",
                    passed=False,
                    output="Logout failed",
                    duration=0.2,
                ),
            ],
            all_passed=False,
        )

        contexts = build_failure_context(sample_tree_with_evidence, evidence_results)

        assert len(contexts) == 1
        ctx = contexts[0]
        assert ctx.intention_id == "INT-2026-01-30-0005"
        assert ctx.intention_title == "Auth Tests"
        assert len(ctx.failed_tests) == 2
        assert "tests/test_auth.py::test_login" in ctx.failed_tests
        assert "tests/test_auth.py::test_logout" in ctx.failed_tests

    def test_duplicate_failures_not_repeated(self, sample_tree_with_evidence: Intention) -> None:
        """Test that duplicate failures are not added multiple times."""
        evidence_results = EvidenceResults(
            results=[
                EvidenceResult(
                    selector="tests/test_auth.py::test_login",
                    passed=False,
                ),
                EvidenceResult(
                    selector="tests/test_auth.py::test_login",
                    passed=False,
                ),
            ],
            all_passed=False,
        )

        contexts = build_failure_context(sample_tree_with_evidence, evidence_results)

        assert len(contexts) == 1
        assert len(contexts[0].failed_tests) == 1


class TestBuildFailureContextCrossIntentions:
    """Tests for failures across different intentions."""

    def test_failures_across_different_intentions(
        self, multi_functionality_tree: Intention
    ) -> None:
        """Test that failures from different intentions create separate contexts."""
        evidence_results = EvidenceResults(
            results=[
                EvidenceResult(
                    selector="tests/test_auth.py::test_login",
                    passed=False,
                ),
                EvidenceResult(
                    selector="tests/test_payment.py::test_process",
                    passed=False,
                ),
            ],
            all_passed=False,
        )

        contexts = build_failure_context(multi_functionality_tree, evidence_results)

        assert len(contexts) == 2

        # Find contexts by intention ID
        context_map = {ctx.intention_id: ctx for ctx in contexts}

        auth_ctx = context_map["INT-2026-01-30-0010"]
        assert auth_ctx.intention_title == "Auth Tests"
        assert auth_ctx.code_scope == ["src/auth/"]
        assert "tests/test_auth.py::test_login" in auth_ctx.failed_tests

        payment_ctx = context_map["INT-2026-01-30-0020"]
        assert payment_ctx.intention_title == "Payment Tests"
        assert payment_ctx.code_scope == ["src/payment/"]
        assert "tests/test_payment.py::test_process" in payment_ctx.failed_tests


class TestBuildFailureContextRendering:
    """Tests for output format and rendering."""

    def test_failure_context_dataclass_fields(self, sample_tree_with_evidence: Intention) -> None:
        """Verify IntentionFailureContext has all expected fields."""
        evidence_results = EvidenceResults(
            results=[
                EvidenceResult(
                    selector="tests/test_feature.py::test_add",
                    passed=False,
                )
            ],
            all_passed=False,
        )

        contexts = build_failure_context(sample_tree_with_evidence, evidence_results)

        assert len(contexts) == 1
        ctx = contexts[0]

        # Verify all fields are present and have correct types
        assert isinstance(ctx.intention_id, str)
        assert isinstance(ctx.intention_title, str)
        assert isinstance(ctx.intention_path, str)
        assert isinstance(ctx.failed_tests, list)
        assert isinstance(ctx.linked_docs, list)
        assert isinstance(ctx.code_scope, list)

    def test_failure_context_can_be_instantiated_directly(self) -> None:
        """Test that IntentionFailureContext can be created directly."""
        ctx = IntentionFailureContext(
            intention_id="INT-TEST-001",
            intention_title="Test Intention",
            intention_path="Goal/Feature/Test",
            failed_tests=["test::selector"],
            linked_docs=["doc.md"],
            code_scope=["src/"],
        )

        assert ctx.intention_id == "INT-TEST-001"
        assert ctx.intention_title == "Test Intention"
        assert ctx.intention_path == "Goal/Feature/Test"
        assert ctx.failed_tests == ["test::selector"]
        assert ctx.linked_docs == ["doc.md"]
        assert ctx.code_scope == ["src/"]


class TestBuildFailureContextMissingDocs:
    """Tests for graceful handling of missing supporting_docs."""

    def test_empty_supporting_docs(self) -> None:
        """Test that empty supporting_docs results in empty linked_docs."""
        intention = Intention(
            id="INT-2026-01-30-0001",
            title="No Docs",
            kind=IntentionKind.IMPLEMENTATION,
            status=IntentionStatus.IMPLEMENTED,
            evidence_tests=["tests/test_nodocs.py::test_one"],
            supporting_docs=[],  # Empty docs
        )
        root = Intention(
            id="INT-2026-01-30-0000",
            title="Root",
            kind=IntentionKind.FUNCTIONALITY,
            status=IntentionStatus.IMPLEMENTED,
            code_home=["src/"],
            children=[intention],
        )

        evidence_results = EvidenceResults(
            results=[
                EvidenceResult(
                    selector="tests/test_nodocs.py::test_one",
                    passed=False,
                )
            ],
            all_passed=False,
        )

        contexts = build_failure_context(root, evidence_results)

        assert len(contexts) == 1
        assert contexts[0].linked_docs == []

    def test_missing_supporting_docs_field(self) -> None:
        """Test that default empty supporting_docs is handled."""
        intention = Intention(
            id="INT-2026-01-30-0001",
            title="Default Docs",
            kind=IntentionKind.IMPLEMENTATION,
            status=IntentionStatus.IMPLEMENTED,
            evidence_tests=["tests/test_default.py::test_one"],
            # supporting_docs not specified, defaults to []
        )
        root = Intention(
            id="INT-2026-01-30-0000",
            title="Root",
            kind=IntentionKind.FUNCTIONALITY,
            status=IntentionStatus.IMPLEMENTED,
            code_home=["src/"],
            children=[intention],
        )

        evidence_results = EvidenceResults(
            results=[
                EvidenceResult(
                    selector="tests/test_default.py::test_one",
                    passed=False,
                )
            ],
            all_passed=False,
        )

        contexts = build_failure_context(root, evidence_results)

        assert len(contexts) == 1
        assert contexts[0].linked_docs == []


class TestBuildFailureContextNoFailures:
    """Tests for all-passing scenario."""

    def test_no_failures_returns_empty_list(self, sample_tree_with_evidence: Intention) -> None:
        """Test that all passing tests results in empty context list."""
        evidence_results = EvidenceResults(
            results=[
                EvidenceResult(
                    selector="tests/test_feature.py::test_add",
                    passed=True,
                    duration=0.1,
                ),
                EvidenceResult(
                    selector="tests/test_auth.py::test_login",
                    passed=True,
                    duration=0.2,
                ),
            ],
            all_passed=True,
        )

        contexts = build_failure_context(sample_tree_with_evidence, evidence_results)

        assert contexts == []

    def test_empty_results_returns_empty_list(self, sample_tree_with_evidence: Intention) -> None:
        """Test that empty evidence results returns empty context list."""
        evidence_results = EvidenceResults(
            results=[],
            all_passed=True,
        )

        contexts = build_failure_context(sample_tree_with_evidence, evidence_results)

        assert contexts == []


class TestBuildFailureContextEdgeCases:
    """Tests for edge cases and error handling."""

    def test_failure_not_linked_to_any_intention(
        self, sample_tree_with_evidence: Intention
    ) -> None:
        """Test that failure for unlinked test produces no context."""
        evidence_results = EvidenceResults(
            results=[
                EvidenceResult(
                    selector="tests/test_unlinked.py::test_orphan",
                    passed=False,
                )
            ],
            all_passed=False,
        )

        contexts = build_failure_context(sample_tree_with_evidence, evidence_results)

        assert contexts == []

    def test_error_results_are_included(self, sample_tree_with_evidence: Intention) -> None:
        """Test that errored tests (not just assertion failures) are included."""
        evidence_results = EvidenceResults(
            results=[
                EvidenceResult(
                    selector="tests/test_feature.py::test_add",
                    passed=False,
                    error_message="ImportError: No module named 'missing'",
                )
            ],
            all_passed=False,
        )

        contexts = build_failure_context(sample_tree_with_evidence, evidence_results)

        assert len(contexts) == 1
        assert "tests/test_feature.py::test_add" in contexts[0].failed_tests

    def test_mixed_pass_fail_results(self, sample_tree_with_evidence: Intention) -> None:
        """Test with mix of passed and failed tests."""
        evidence_results = EvidenceResults(
            results=[
                EvidenceResult(
                    selector="tests/test_feature.py::test_add",
                    passed=True,
                ),
                EvidenceResult(
                    selector="tests/test_auth.py::test_login",
                    passed=False,
                ),
                EvidenceResult(
                    selector="tests/test_auth.py::test_logout",
                    passed=True,
                ),
            ],
            all_passed=False,
        )

        contexts = build_failure_context(sample_tree_with_evidence, evidence_results)

        assert len(contexts) == 1
        assert contexts[0].intention_id == "INT-2026-01-30-0005"
        assert len(contexts[0].failed_tests) == 1
        assert "tests/test_auth.py::test_login" in contexts[0].failed_tests

    def test_intention_without_functionality_ancestor(self) -> None:
        """Test that intention without functionality ancestor has empty code_scope."""
        goal_with_tests = Intention(
            id="INT-2026-01-30-0001",
            title="Goal With Tests",
            kind=IntentionKind.GOAL,
            status=IntentionStatus.IMPLEMENTED,
            evidence_tests=["tests/test_goal.py::test_one"],
        )

        evidence_results = EvidenceResults(
            results=[
                EvidenceResult(
                    selector="tests/test_goal.py::test_one",
                    passed=False,
                )
            ],
            all_passed=False,
        )

        contexts = build_failure_context(goal_with_tests, evidence_results)

        assert len(contexts) == 1
        assert contexts[0].code_scope == []

    def test_docs_are_copied_not_referenced(self, sample_tree_with_evidence: Intention) -> None:
        """Test that linked_docs is a copy, not a reference to original."""
        evidence_results = EvidenceResults(
            results=[
                EvidenceResult(
                    selector="tests/test_feature.py::test_add",
                    passed=False,
                )
            ],
            all_passed=False,
        )

        contexts = build_failure_context(sample_tree_with_evidence, evidence_results)

        # Modify the returned list
        contexts[0].linked_docs.append("new_doc.md")

        # Original should be unchanged
        from intention_audit.models.tree import find_intention

        impl = find_intention(sample_tree_with_evidence, "INT-2026-01-30-0003")
        assert impl is not None
        assert "new_doc.md" not in impl.supporting_docs

    def test_code_scope_is_copied_not_referenced(self) -> None:
        """Test that code_scope is a copy, not a reference to original."""
        implementation = Intention(
            id="INT-2026-01-30-0003",
            title="Impl",
            kind=IntentionKind.IMPLEMENTATION,
            status=IntentionStatus.IMPLEMENTED,
            evidence_tests=["tests/test.py::test_one"],
        )
        functionality = Intention(
            id="INT-2026-01-30-0002",
            title="Func",
            kind=IntentionKind.FUNCTIONALITY,
            status=IntentionStatus.IMPLEMENTED,
            code_home=["src/original/"],
            children=[implementation],
        )

        evidence_results = EvidenceResults(
            results=[
                EvidenceResult(
                    selector="tests/test.py::test_one",
                    passed=False,
                )
            ],
            all_passed=False,
        )

        contexts = build_failure_context(functionality, evidence_results)

        # Modify the returned list
        contexts[0].code_scope.append("src/new/")

        # Original should be unchanged
        assert "src/new/" not in functionality.code_home
