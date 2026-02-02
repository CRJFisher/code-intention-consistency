"""Unit tests for intention tree utilities."""

import pytest

from intention_audit.models.intention import Intention, IntentionKind, IntentionStatus
from intention_audit.models.tree import (
    find_functionality_ancestor,
    find_intention,
    get_all_intent_ids,
    get_intention_path,
    get_intentions_by_kind,
    validate_intent_id_exists,
)


@pytest.fixture
def sample_tree() -> Intention:
    """Create a sample intention tree for testing."""
    implementation = Intention(
        id="INT-2026-01-30-0003",
        title="Add Feature",
        kind=IntentionKind.IMPLEMENTATION,
        status=IntentionStatus.IMPLEMENTED,
    )
    tests = Intention(
        id="INT-2026-01-30-0004",
        title="Test Feature",
        kind=IntentionKind.TESTS,
        status=IntentionStatus.IMPLEMENTED,
    )
    functionality = Intention(
        id="INT-2026-01-30-0002",
        title="User Authentication",
        kind=IntentionKind.FUNCTIONALITY,
        status=IntentionStatus.IN_PROGRESS,
        code_home=["src/auth/"],
        children=[implementation, tests],
    )
    goal = Intention(
        id="INT-2026-01-30-0001",
        title="Security Goal",
        kind=IntentionKind.GOAL,
        status=IntentionStatus.PLANNED,
        children=[functionality],
    )
    return goal


class TestFindIntention:
    """Tests for find_intention function."""

    def test_find_root(self, sample_tree: Intention):
        """Test finding the root intention."""
        result = find_intention(sample_tree, "INT-2026-01-30-0001")
        assert result is not None
        assert result.title == "Security Goal"

    def test_find_child(self, sample_tree: Intention):
        """Test finding a child intention."""
        result = find_intention(sample_tree, "INT-2026-01-30-0002")
        assert result is not None
        assert result.title == "User Authentication"

    def test_find_grandchild(self, sample_tree: Intention):
        """Test finding a grandchild intention."""
        result = find_intention(sample_tree, "INT-2026-01-30-0003")
        assert result is not None
        assert result.title == "Add Feature"

    def test_find_nonexistent(self, sample_tree: Intention):
        """Test searching for non-existent intention."""
        result = find_intention(sample_tree, "INT-9999-99-99-9999")
        assert result is None


class TestFindFunctionalityAncestor:
    """Tests for find_functionality_ancestor function."""

    def test_find_from_implementation(self, sample_tree: Intention):
        """Test finding functionality ancestor from implementation."""
        result = find_functionality_ancestor(sample_tree, "INT-2026-01-30-0003")
        assert result is not None
        assert result.id == "INT-2026-01-30-0002"
        assert result.kind == IntentionKind.FUNCTIONALITY

    def test_find_from_tests(self, sample_tree: Intention):
        """Test finding functionality ancestor from tests."""
        result = find_functionality_ancestor(sample_tree, "INT-2026-01-30-0004")
        assert result is not None
        assert result.id == "INT-2026-01-30-0002"

    def test_functionality_returns_self(self, sample_tree: Intention):
        """Test that functionality intention returns itself."""
        result = find_functionality_ancestor(sample_tree, "INT-2026-01-30-0002")
        assert result is not None
        assert result.id == "INT-2026-01-30-0002"

    def test_goal_has_no_functionality_ancestor(self, sample_tree: Intention):
        """Test that goal has no functionality ancestor."""
        result = find_functionality_ancestor(sample_tree, "INT-2026-01-30-0001")
        assert result is None

    def test_nonexistent_intention(self, sample_tree: Intention):
        """Test with non-existent intention."""
        result = find_functionality_ancestor(sample_tree, "INT-9999-99-99-9999")
        assert result is None


class TestGetIntentionPath:
    """Tests for get_intention_path function."""

    def test_root_path(self, sample_tree: Intention):
        """Test path for root intention."""
        result = get_intention_path(sample_tree, "INT-2026-01-30-0001")
        assert result == "Security Goal"

    def test_child_path(self, sample_tree: Intention):
        """Test path for child intention."""
        result = get_intention_path(sample_tree, "INT-2026-01-30-0002")
        assert result == "Security Goal/User Authentication"

    def test_grandchild_path(self, sample_tree: Intention):
        """Test path for grandchild intention."""
        result = get_intention_path(sample_tree, "INT-2026-01-30-0003")
        assert result == "Security Goal/User Authentication/Add Feature"

    def test_nonexistent_returns_none(self, sample_tree: Intention):
        """Test that non-existent intention returns None."""
        result = get_intention_path(sample_tree, "INT-9999-99-99-9999")
        assert result is None


class TestValidateIntentIdExists:
    """Tests for validate_intent_id_exists function."""

    def test_root_exists(self, sample_tree: Intention):
        """Test that root ID exists."""
        assert validate_intent_id_exists(sample_tree, "INT-2026-01-30-0001") is True

    def test_child_exists(self, sample_tree: Intention):
        """Test that child ID exists."""
        assert validate_intent_id_exists(sample_tree, "INT-2026-01-30-0002") is True

    def test_grandchild_exists(self, sample_tree: Intention):
        """Test that grandchild ID exists."""
        assert validate_intent_id_exists(sample_tree, "INT-2026-01-30-0003") is True

    def test_nonexistent_returns_false(self, sample_tree: Intention):
        """Test that non-existent ID returns False."""
        assert validate_intent_id_exists(sample_tree, "INT-9999-99-99-9999") is False


class TestGetAllIntentIds:
    """Tests for get_all_intent_ids function."""

    def test_gets_all_ids(self, sample_tree: Intention):
        """Test that all IDs are returned."""
        ids = get_all_intent_ids(sample_tree)
        assert len(ids) == 4
        assert "INT-2026-01-30-0001" in ids
        assert "INT-2026-01-30-0002" in ids
        assert "INT-2026-01-30-0003" in ids
        assert "INT-2026-01-30-0004" in ids

    def test_single_node(self):
        """Test with single node tree."""
        single = Intention(
            id="INT-2026-01-30-0001",
            title="Single",
            kind=IntentionKind.GOAL,
        )
        ids = get_all_intent_ids(single)
        assert ids == ["INT-2026-01-30-0001"]


class TestGetIntentionsByKind:
    """Tests for get_intentions_by_kind function."""

    def test_get_goals(self, sample_tree: Intention):
        """Test getting all goals."""
        goals = get_intentions_by_kind(sample_tree, IntentionKind.GOAL)
        assert len(goals) == 1
        assert goals[0].title == "Security Goal"

    def test_get_functionality(self, sample_tree: Intention):
        """Test getting all functionality intentions."""
        funcs = get_intentions_by_kind(sample_tree, IntentionKind.FUNCTIONALITY)
        assert len(funcs) == 1
        assert funcs[0].title == "User Authentication"

    def test_get_implementations(self, sample_tree: Intention):
        """Test getting all implementations."""
        impls = get_intentions_by_kind(sample_tree, IntentionKind.IMPLEMENTATION)
        assert len(impls) == 1
        assert impls[0].title == "Add Feature"

    def test_get_nonexistent_kind(self, sample_tree: Intention):
        """Test getting kind that doesn't exist in tree."""
        docs = get_intentions_by_kind(sample_tree, IntentionKind.DOCS)
        assert docs == []


class TestDeepTree:
    """Tests with deeply nested intention trees."""

    def test_deep_nesting(self):
        """Test with deeply nested tree."""
        level4 = Intention(id="L4", title="Level 4", kind=IntentionKind.IMPLEMENTATION)
        level3 = Intention(
            id="L3", title="Level 3", kind=IntentionKind.FUNCTIONALITY, children=[level4]
        )
        level2 = Intention(
            id="L2", title="Level 2", kind=IntentionKind.FUNCTIONALITY, children=[level3]
        )
        level1 = Intention(id="L1", title="Level 1", kind=IntentionKind.GOAL, children=[level2])

        assert find_intention(level1, "L4") is not None
        assert get_intention_path(level1, "L4") == "Level 1/Level 2/Level 3/Level 4"

        # Finding functionality ancestor from L4 should find L3 (immediate parent)
        func = find_functionality_ancestor(level1, "L4")
        assert func is not None
        assert func.id == "L3"
