"""Unit tests for code_home boundary checker."""

from intention_audit.models.commit_plan import CommitEntry, CommitPlan
from intention_audit.models.intention import Intention, IntentionKind
from intention_audit.structure.boundary import (
    BoundaryViolation,
    _find_functionality_ancestor,
    _find_intention_by_id,
    _path_within_prefixes,
    check_code_home_boundaries,
)


class TestBoundaryViolation:
    """Tests for BoundaryViolation dataclass."""

    def test_instantiation(self) -> None:
        """Test creating a BoundaryViolation with all fields."""
        violation = BoundaryViolation(
            commit_entry_index=0,
            intent_id="INT-2026-01-30-0001",
            functionality_intent_id="INT-2026-01-30-0002",
            violating_paths=["outside/file.py"],
            expected_prefixes=["src/feature/"],
            suggested_fix="Move files to src/feature/",
        )
        assert violation.commit_entry_index == 0
        assert violation.intent_id == "INT-2026-01-30-0001"
        assert violation.functionality_intent_id == "INT-2026-01-30-0002"
        assert violation.violating_paths == ["outside/file.py"]
        assert violation.expected_prefixes == ["src/feature/"]
        assert violation.suggested_fix == "Move files to src/feature/"

    def test_default_suggested_fix(self) -> None:
        """Test suggested_fix defaults to empty string."""
        violation = BoundaryViolation(
            commit_entry_index=0,
            intent_id="INT-2026-01-30-0001",
            functionality_intent_id=None,
            violating_paths=[],
            expected_prefixes=[],
        )
        assert violation.suggested_fix == ""


class TestPathWithinPrefixes:
    """Tests for _path_within_prefixes helper function."""

    def test_path_within_single_prefix(self) -> None:
        """Test path that matches a single prefix."""
        assert _path_within_prefixes("src/feature/module.py", ["src/feature/"])
        assert _path_within_prefixes("src/feature/sub/module.py", ["src/feature/"])

    def test_path_outside_prefix(self) -> None:
        """Test path that doesn't match any prefix."""
        assert not _path_within_prefixes("other/module.py", ["src/feature/"])
        assert not _path_within_prefixes("src/other/module.py", ["src/feature/"])

    def test_path_within_multiple_prefixes(self) -> None:
        """Test path matching one of multiple prefixes."""
        prefixes = ["src/feature/", "tests/feature/"]
        assert _path_within_prefixes("src/feature/module.py", prefixes)
        assert _path_within_prefixes("tests/feature/test_module.py", prefixes)
        assert not _path_within_prefixes("docs/feature.md", prefixes)

    def test_prefix_without_trailing_slash(self) -> None:
        """Test that prefixes without trailing slash work correctly."""
        assert _path_within_prefixes("src/feature/module.py", ["src/feature"])

    def test_exact_prefix_match(self) -> None:
        """Test path that exactly matches the prefix directory."""
        assert _path_within_prefixes("src/feature", ["src/feature/"])

    def test_partial_name_no_match(self) -> None:
        """Test that partial directory name matches don't count."""
        # 'src/featureX/file.py' should NOT match 'src/feature/'
        assert not _path_within_prefixes("src/featureX/file.py", ["src/feature"])


class TestFindIntentionById:
    """Tests for _find_intention_by_id helper function."""

    def test_find_root(self) -> None:
        """Test finding the root node itself."""
        root = Intention(
            id="INT-2026-01-30-0001",
            title="Root",
            kind=IntentionKind.GOAL,
        )
        found = _find_intention_by_id(root, "INT-2026-01-30-0001")
        assert found is root

    def test_find_child(self) -> None:
        """Test finding a direct child."""
        child = Intention(
            id="INT-2026-01-30-0002",
            title="Child",
            kind=IntentionKind.FUNCTIONALITY,
        )
        root = Intention(
            id="INT-2026-01-30-0001",
            title="Root",
            kind=IntentionKind.GOAL,
            children=[child],
        )
        found = _find_intention_by_id(root, "INT-2026-01-30-0002")
        assert found is child

    def test_find_deeply_nested(self) -> None:
        """Test finding deeply nested node."""
        leaf = Intention(
            id="INT-2026-01-30-0004",
            title="Leaf",
            kind=IntentionKind.IMPLEMENTATION,
        )
        impl = Intention(
            id="INT-2026-01-30-0003",
            title="Implementation",
            kind=IntentionKind.IMPLEMENTATION,
            children=[leaf],
        )
        func = Intention(
            id="INT-2026-01-30-0002",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            children=[impl],
        )
        root = Intention(
            id="INT-2026-01-30-0001",
            title="Goal",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        found = _find_intention_by_id(root, "INT-2026-01-30-0004")
        assert found is leaf

    def test_not_found(self) -> None:
        """Test when ID doesn't exist in tree."""
        root = Intention(
            id="INT-2026-01-30-0001",
            title="Root",
            kind=IntentionKind.GOAL,
        )
        found = _find_intention_by_id(root, "INT-NONEXISTENT")
        assert found is None


class TestFindFunctionalityAncestor:
    """Tests for _find_functionality_ancestor helper function."""

    def test_direct_parent_functionality(self) -> None:
        """Test finding functionality that is direct parent."""
        impl = Intention(
            id="INT-2026-01-30-0002",
            title="Implementation",
            kind=IntentionKind.IMPLEMENTATION,
        )
        func = Intention(
            id="INT-2026-01-30-0001",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            code_home=["src/feature/"],
            children=[impl],
        )
        root = Intention(
            id="INT-2026-01-30-0000",
            title="Root",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        found = _find_functionality_ancestor(root, "INT-2026-01-30-0002")
        assert found is func

    def test_grandparent_functionality(self) -> None:
        """Test finding functionality that is grandparent."""
        leaf = Intention(
            id="INT-2026-01-30-0003",
            title="Leaf",
            kind=IntentionKind.IMPLEMENTATION,
        )
        impl = Intention(
            id="INT-2026-01-30-0002",
            title="Implementation",
            kind=IntentionKind.IMPLEMENTATION,
            children=[leaf],
        )
        func = Intention(
            id="INT-2026-01-30-0001",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            code_home=["src/feature/"],
            children=[impl],
        )
        root = Intention(
            id="INT-2026-01-30-0000",
            title="Root",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        found = _find_functionality_ancestor(root, "INT-2026-01-30-0003")
        assert found is func

    def test_no_functionality_ancestor(self) -> None:
        """Test when there is no functionality ancestor."""
        impl = Intention(
            id="INT-2026-01-30-0002",
            title="Implementation",
            kind=IntentionKind.IMPLEMENTATION,
        )
        root = Intention(
            id="INT-2026-01-30-0001",
            title="Root",
            kind=IntentionKind.GOAL,
            children=[impl],
        )
        found = _find_functionality_ancestor(root, "INT-2026-01-30-0002")
        assert found is None

    def test_intent_not_found(self) -> None:
        """Test when the intent ID doesn't exist."""
        root = Intention(
            id="INT-2026-01-30-0001",
            title="Root",
            kind=IntentionKind.GOAL,
        )
        found = _find_functionality_ancestor(root, "INT-NONEXISTENT")
        assert found is None

    def test_functionality_is_not_self(self) -> None:
        """Test that searching for a functionality node doesn't return itself."""
        func = Intention(
            id="INT-2026-01-30-0002",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            code_home=["src/feature/"],
        )
        root = Intention(
            id="INT-2026-01-30-0001",
            title="Root",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        # Looking for ancestor of functionality should not return itself
        found = _find_functionality_ancestor(root, "INT-2026-01-30-0002")
        assert found is None  # No functionality *ancestor* exists


class TestCheckCodeHomeBoundaries:
    """Tests for check_code_home_boundaries function."""

    def test_no_violation_within_code_home(self) -> None:
        """Test that files within code_home produce no violations."""
        impl = Intention(
            id="INT-2026-01-30-0002",
            title="Implementation",
            kind=IntentionKind.IMPLEMENTATION,
        )
        func = Intention(
            id="INT-2026-01-30-0001",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            code_home=["src/feature/"],
            children=[impl],
        )
        root = Intention(
            id="INT-2026-01-30-0000",
            title="Root",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        plan = CommitPlan(
            version=1,
            ready=True,
            commits=[
                CommitEntry(
                    intent_id="INT-2026-01-30-0002",
                    subject="Add feature module",
                    patch="",
                    files=["src/feature/module.py", "src/feature/utils.py"],
                )
            ],
        )
        violations = check_code_home_boundaries(root, plan)
        assert violations == []

    def test_violation_outside_code_home(self) -> None:
        """Test that files outside code_home produce a violation."""
        impl = Intention(
            id="INT-2026-01-30-0002",
            title="Implementation",
            kind=IntentionKind.IMPLEMENTATION,
        )
        func = Intention(
            id="INT-2026-01-30-0001",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            code_home=["src/feature/"],
            children=[impl],
        )
        root = Intention(
            id="INT-2026-01-30-0000",
            title="Root",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        plan = CommitPlan(
            version=1,
            ready=True,
            commits=[
                CommitEntry(
                    intent_id="INT-2026-01-30-0002",
                    subject="Add feature module",
                    patch="",
                    files=["src/other/module.py"],  # Outside code_home
                )
            ],
        )
        violations = check_code_home_boundaries(root, plan)
        assert len(violations) == 1
        assert violations[0].commit_entry_index == 0
        assert violations[0].intent_id == "INT-2026-01-30-0002"
        assert violations[0].functionality_intent_id == "INT-2026-01-30-0001"
        assert violations[0].violating_paths == ["src/other/module.py"]
        assert violations[0].expected_prefixes == ["src/feature/"]
        assert "src/feature/" in violations[0].suggested_fix

    def test_multiple_code_home_prefixes(self) -> None:
        """Test with multiple code_home prefixes."""
        impl = Intention(
            id="INT-2026-01-30-0002",
            title="Implementation",
            kind=IntentionKind.IMPLEMENTATION,
        )
        func = Intention(
            id="INT-2026-01-30-0001",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            code_home=["src/feature/", "tests/feature/"],
            children=[impl],
        )
        root = Intention(
            id="INT-2026-01-30-0000",
            title="Root",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        plan = CommitPlan(
            version=1,
            ready=True,
            commits=[
                CommitEntry(
                    intent_id="INT-2026-01-30-0002",
                    subject="Add feature with tests",
                    patch="",
                    files=[
                        "src/feature/module.py",
                        "tests/feature/test_module.py",
                    ],
                )
            ],
        )
        violations = check_code_home_boundaries(root, plan)
        assert violations == []

    def test_multiple_prefixes_partial_violation(self) -> None:
        """Test that some files violate while others don't with multiple prefixes."""
        impl = Intention(
            id="INT-2026-01-30-0002",
            title="Implementation",
            kind=IntentionKind.IMPLEMENTATION,
        )
        func = Intention(
            id="INT-2026-01-30-0001",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            code_home=["src/feature/", "tests/feature/"],
            children=[impl],
        )
        root = Intention(
            id="INT-2026-01-30-0000",
            title="Root",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        plan = CommitPlan(
            version=1,
            ready=True,
            commits=[
                CommitEntry(
                    intent_id="INT-2026-01-30-0002",
                    subject="Add feature",
                    patch="",
                    files=[
                        "src/feature/module.py",
                        "docs/feature.md",  # Violates
                    ],
                )
            ],
        )
        violations = check_code_home_boundaries(root, plan)
        assert len(violations) == 1
        assert violations[0].violating_paths == ["docs/feature.md"]

    def test_nested_functionality_intentions(self) -> None:
        """Test deep tree traversal for nested functionality intentions."""
        leaf = Intention(
            id="INT-2026-01-30-0004",
            title="Deep Leaf",
            kind=IntentionKind.IMPLEMENTATION,
        )
        tests = Intention(
            id="INT-2026-01-30-0003",
            title="Tests",
            kind=IntentionKind.TESTS,
            children=[leaf],
        )
        func = Intention(
            id="INT-2026-01-30-0002",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            code_home=["src/deep/"],
            children=[tests],
        )
        root = Intention(
            id="INT-2026-01-30-0001",
            title="Goal",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        plan = CommitPlan(
            version=1,
            ready=True,
            commits=[
                CommitEntry(
                    intent_id="INT-2026-01-30-0004",
                    subject="Add deep implementation",
                    patch="",
                    files=["src/deep/nested/module.py"],
                )
            ],
        )
        violations = check_code_home_boundaries(root, plan)
        assert violations == []

    def test_nested_with_violation(self) -> None:
        """Test nested tree with violation."""
        leaf = Intention(
            id="INT-2026-01-30-0004",
            title="Deep Leaf",
            kind=IntentionKind.IMPLEMENTATION,
        )
        tests = Intention(
            id="INT-2026-01-30-0003",
            title="Tests",
            kind=IntentionKind.TESTS,
            children=[leaf],
        )
        func = Intention(
            id="INT-2026-01-30-0002",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            code_home=["src/deep/"],
            children=[tests],
        )
        root = Intention(
            id="INT-2026-01-30-0001",
            title="Goal",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        plan = CommitPlan(
            version=1,
            ready=True,
            commits=[
                CommitEntry(
                    intent_id="INT-2026-01-30-0004",
                    subject="Add deep implementation",
                    patch="",
                    files=["src/shallow/module.py"],  # Wrong directory
                )
            ],
        )
        violations = check_code_home_boundaries(root, plan)
        assert len(violations) == 1
        assert violations[0].intent_id == "INT-2026-01-30-0004"
        assert violations[0].functionality_intent_id == "INT-2026-01-30-0002"

    def test_no_code_home_defined_skip(self) -> None:
        """Test graceful skip when no code_home is defined."""
        impl = Intention(
            id="INT-2026-01-30-0002",
            title="Implementation",
            kind=IntentionKind.IMPLEMENTATION,
        )
        func = Intention(
            id="INT-2026-01-30-0001",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            # No code_home defined
            children=[impl],
        )
        root = Intention(
            id="INT-2026-01-30-0000",
            title="Root",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        plan = CommitPlan(
            version=1,
            ready=True,
            commits=[
                CommitEntry(
                    intent_id="INT-2026-01-30-0002",
                    subject="Add module anywhere",
                    patch="",
                    files=["anywhere/module.py"],
                )
            ],
        )
        violations = check_code_home_boundaries(root, plan)
        assert violations == []

    def test_missing_functionality_ancestor_skip(self) -> None:
        """Test graceful handling when no functionality ancestor exists."""
        impl = Intention(
            id="INT-2026-01-30-0002",
            title="Implementation",
            kind=IntentionKind.IMPLEMENTATION,
        )
        root = Intention(
            id="INT-2026-01-30-0001",
            title="Goal",
            kind=IntentionKind.GOAL,
            children=[impl],
        )
        plan = CommitPlan(
            version=1,
            ready=True,
            commits=[
                CommitEntry(
                    intent_id="INT-2026-01-30-0002",
                    subject="Add something",
                    patch="",
                    files=["anywhere/module.py"],
                )
            ],
        )
        violations = check_code_home_boundaries(root, plan)
        assert violations == []

    def test_explicit_functionality_intent_id(self) -> None:
        """Test using explicit functionality_intent_id from CommitEntry."""
        impl = Intention(
            id="INT-2026-01-30-0003",
            title="Implementation",
            kind=IntentionKind.IMPLEMENTATION,
        )
        func = Intention(
            id="INT-2026-01-30-0002",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            code_home=["src/feature/"],
            children=[impl],
        )
        root = Intention(
            id="INT-2026-01-30-0001",
            title="Goal",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        plan = CommitPlan(
            version=1,
            ready=True,
            commits=[
                CommitEntry(
                    intent_id="INT-2026-01-30-0003",
                    subject="Add feature",
                    patch="",
                    functionality_intent_id="INT-2026-01-30-0002",  # Explicit
                    files=["src/feature/module.py"],
                )
            ],
        )
        violations = check_code_home_boundaries(root, plan)
        assert violations == []

    def test_explicit_functionality_intent_id_violation(self) -> None:
        """Test violation with explicit functionality_intent_id."""
        impl = Intention(
            id="INT-2026-01-30-0003",
            title="Implementation",
            kind=IntentionKind.IMPLEMENTATION,
        )
        func = Intention(
            id="INT-2026-01-30-0002",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            code_home=["src/feature/"],
            children=[impl],
        )
        root = Intention(
            id="INT-2026-01-30-0001",
            title="Goal",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        plan = CommitPlan(
            version=1,
            ready=True,
            commits=[
                CommitEntry(
                    intent_id="INT-2026-01-30-0003",
                    subject="Add feature",
                    patch="",
                    functionality_intent_id="INT-2026-01-30-0002",
                    files=["src/other/module.py"],  # Violates
                )
            ],
        )
        violations = check_code_home_boundaries(root, plan)
        assert len(violations) == 1
        assert violations[0].functionality_intent_id == "INT-2026-01-30-0002"

    def test_multiple_commits_mixed_violations(self) -> None:
        """Test multiple commits where some violate and some don't."""
        impl1 = Intention(
            id="INT-2026-01-30-0003",
            title="Implementation 1",
            kind=IntentionKind.IMPLEMENTATION,
        )
        impl2 = Intention(
            id="INT-2026-01-30-0004",
            title="Implementation 2",
            kind=IntentionKind.IMPLEMENTATION,
        )
        func = Intention(
            id="INT-2026-01-30-0002",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            code_home=["src/feature/"],
            children=[impl1, impl2],
        )
        root = Intention(
            id="INT-2026-01-30-0001",
            title="Goal",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        plan = CommitPlan(
            version=1,
            ready=True,
            commits=[
                CommitEntry(
                    intent_id="INT-2026-01-30-0003",
                    subject="Add feature 1",
                    patch="",
                    files=["src/feature/module1.py"],  # OK
                ),
                CommitEntry(
                    intent_id="INT-2026-01-30-0004",
                    subject="Add feature 2",
                    patch="",
                    files=["src/other/module2.py"],  # Violates
                ),
            ],
        )
        violations = check_code_home_boundaries(root, plan)
        assert len(violations) == 1
        assert violations[0].commit_entry_index == 1
        assert violations[0].intent_id == "INT-2026-01-30-0004"

    def test_empty_commit_plan(self) -> None:
        """Test with empty commit plan."""
        root = Intention(
            id="INT-2026-01-30-0001",
            title="Goal",
            kind=IntentionKind.GOAL,
        )
        plan = CommitPlan(
            version=1,
            ready=True,
            commits=[],
        )
        violations = check_code_home_boundaries(root, plan)
        assert violations == []

    def test_empty_files_list(self) -> None:
        """Test commit entry with empty files list."""
        impl = Intention(
            id="INT-2026-01-30-0002",
            title="Implementation",
            kind=IntentionKind.IMPLEMENTATION,
        )
        func = Intention(
            id="INT-2026-01-30-0001",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            code_home=["src/feature/"],
            children=[impl],
        )
        root = Intention(
            id="INT-2026-01-30-0000",
            title="Root",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        plan = CommitPlan(
            version=1,
            ready=True,
            commits=[
                CommitEntry(
                    intent_id="INT-2026-01-30-0002",
                    subject="Empty commit",
                    patch="",
                    files=[],  # Empty
                )
            ],
        )
        violations = check_code_home_boundaries(root, plan)
        assert violations == []

    def test_intent_not_found_in_tree(self) -> None:
        """Test graceful handling when intent_id not found in tree."""
        func = Intention(
            id="INT-2026-01-30-0001",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            code_home=["src/feature/"],
        )
        root = Intention(
            id="INT-2026-01-30-0000",
            title="Root",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        plan = CommitPlan(
            version=1,
            ready=True,
            commits=[
                CommitEntry(
                    intent_id="INT-NONEXISTENT",  # Not in tree
                    subject="Unknown intent",
                    patch="",
                    files=["src/other/module.py"],
                )
            ],
        )
        violations = check_code_home_boundaries(root, plan)
        # Should skip because no functionality ancestor found
        assert violations == []

    def test_multiple_violations_in_single_commit(self) -> None:
        """Test multiple files violating in a single commit."""
        impl = Intention(
            id="INT-2026-01-30-0002",
            title="Implementation",
            kind=IntentionKind.IMPLEMENTATION,
        )
        func = Intention(
            id="INT-2026-01-30-0001",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            code_home=["src/feature/"],
            children=[impl],
        )
        root = Intention(
            id="INT-2026-01-30-0000",
            title="Root",
            kind=IntentionKind.GOAL,
            children=[func],
        )
        plan = CommitPlan(
            version=1,
            ready=True,
            commits=[
                CommitEntry(
                    intent_id="INT-2026-01-30-0002",
                    subject="Add files",
                    patch="",
                    files=[
                        "src/other/file1.py",  # Violates
                        "src/feature/ok.py",  # OK
                        "docs/readme.md",  # Violates
                    ],
                )
            ],
        )
        violations = check_code_home_boundaries(root, plan)
        assert len(violations) == 1
        assert set(violations[0].violating_paths) == {"src/other/file1.py", "docs/readme.md"}
