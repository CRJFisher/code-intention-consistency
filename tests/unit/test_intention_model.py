"""Unit tests for Intention model."""


from intention_audit.models.intention import Intention, IntentionKind, IntentionStatus


class TestIntentionKind:
    """Tests for IntentionKind enum."""

    def test_all_kinds_exist(self):
        """Verify all expected kinds are defined."""
        kinds = {k.value for k in IntentionKind}
        expected = {"goal", "functionality", "implementation", "tests", "docs", "observability"}
        assert kinds == expected

    def test_kind_from_string(self):
        """Test creating kind from string value."""
        assert IntentionKind("goal") == IntentionKind.GOAL
        assert IntentionKind("functionality") == IntentionKind.FUNCTIONALITY
        assert IntentionKind("implementation") == IntentionKind.IMPLEMENTATION


class TestIntentionStatus:
    """Tests for IntentionStatus enum."""

    def test_all_statuses_exist(self):
        """Verify all expected statuses are defined."""
        statuses = {s.value for s in IntentionStatus}
        expected = {"planned", "in_progress", "implemented", "superseded", "deprecated"}
        assert statuses == expected


class TestIntention:
    """Tests for Intention dataclass."""

    def test_minimal_instantiation(self):
        """Test creating intention with only required fields."""
        intent = Intention(
            id="INT-2026-01-30-0001",
            title="Test Intention",
            kind=IntentionKind.IMPLEMENTATION,
        )
        assert intent.id == "INT-2026-01-30-0001"
        assert intent.title == "Test Intention"
        assert intent.kind == IntentionKind.IMPLEMENTATION
        assert intent.status == IntentionStatus.PLANNED  # default
        assert intent.children == []

    def test_full_instantiation(self):
        """Test creating intention with all fields."""
        intent = Intention(
            id="INT-2026-01-30-0001",
            title="Full Intention",
            kind=IntentionKind.FUNCTIONALITY,
            status=IntentionStatus.IMPLEMENTED,
            children=[],
            created_at="2026-01-30T10:00:00Z",
            rationale="Because we need it",
            constraints=["Must be fast", "Must be safe"],
            superseded_by=None,
            evidence_tests=["tests/test_x.py::test_something"],
            supporting_docs=["docs/feature.md#section"],
            code_home=["src/feature/"],
            named_scopes=["FeatureX"],
        )
        assert intent.rationale == "Because we need it"
        assert intent.constraints == ["Must be fast", "Must be safe"]
        assert intent.evidence_tests == ["tests/test_x.py::test_something"]
        assert intent.code_home == ["src/feature/"]

    def test_nested_children(self):
        """Test intention tree with nested children."""
        leaf = Intention(
            id="INT-2026-01-30-0003",
            title="Leaf",
            kind=IntentionKind.IMPLEMENTATION,
        )
        func = Intention(
            id="INT-2026-01-30-0002",
            title="Feature",
            kind=IntentionKind.FUNCTIONALITY,
            children=[leaf],
        )
        root = Intention(
            id="INT-2026-01-30-0001",
            title="Goal",
            kind=IntentionKind.GOAL,
            children=[func],
        )

        assert len(root.children) == 1
        assert root.children[0].id == "INT-2026-01-30-0002"
        assert len(root.children[0].children) == 1
        assert root.children[0].children[0].id == "INT-2026-01-30-0003"

    def test_from_dict_minimal(self):
        """Test creating intention from minimal dict."""
        data = {
            "id": "INT-2026-01-30-0001",
            "title": "Test",
            "kind": "implementation",
        }
        intent = Intention.from_dict(data)
        assert intent.id == "INT-2026-01-30-0001"
        assert intent.kind == IntentionKind.IMPLEMENTATION
        assert intent.status == IntentionStatus.PLANNED

    def test_from_dict_with_children(self):
        """Test creating intention tree from dict."""
        data = {
            "id": "INT-2026-01-30-0001",
            "title": "Root",
            "kind": "goal",
            "status": "implemented",
            "children": [
                {
                    "id": "INT-2026-01-30-0002",
                    "title": "Child",
                    "kind": "functionality",
                    "code_home": ["src/module/"],
                }
            ],
        }
        intent = Intention.from_dict(data)
        assert len(intent.children) == 1
        assert intent.children[0].code_home == ["src/module/"]

    def test_to_dict_minimal(self):
        """Test converting minimal intention to dict."""
        intent = Intention(
            id="INT-2026-01-30-0001",
            title="Test",
            kind=IntentionKind.IMPLEMENTATION,
        )
        data = intent.to_dict()
        assert data["id"] == "INT-2026-01-30-0001"
        assert data["kind"] == "implementation"
        assert data["status"] == "planned"
        assert "children" not in data  # Empty list not included
        assert "rationale" not in data  # None not included

    def test_to_dict_roundtrip(self):
        """Test dict conversion preserves data."""
        original = Intention(
            id="INT-2026-01-30-0001",
            title="Test",
            kind=IntentionKind.FUNCTIONALITY,
            status=IntentionStatus.IN_PROGRESS,
            rationale="Testing roundtrip",
            code_home=["src/test/"],
            children=[
                Intention(
                    id="INT-2026-01-30-0002",
                    title="Child",
                    kind=IntentionKind.IMPLEMENTATION,
                )
            ],
        )
        data = original.to_dict()
        restored = Intention.from_dict(data)

        assert restored.id == original.id
        assert restored.kind == original.kind
        assert restored.rationale == original.rationale
        assert restored.code_home == original.code_home
        assert len(restored.children) == 1
        assert restored.children[0].id == original.children[0].id

    def test_constraints_as_string(self):
        """Test constraints can be a single string."""
        intent = Intention(
            id="INT-2026-01-30-0001",
            title="Test",
            kind=IntentionKind.IMPLEMENTATION,
            constraints="Single constraint",
        )
        assert intent.constraints == "Single constraint"

    def test_constraints_as_list(self):
        """Test constraints can be a list."""
        intent = Intention(
            id="INT-2026-01-30-0001",
            title="Test",
            kind=IntentionKind.IMPLEMENTATION,
            constraints=["First", "Second"],
        )
        assert intent.constraints == ["First", "Second"]

    def test_optional_fields_default_to_none_or_empty(self):
        """Test optional fields have proper defaults."""
        intent = Intention(
            id="INT-2026-01-30-0001",
            title="Test",
            kind=IntentionKind.IMPLEMENTATION,
        )
        assert intent.created_at is None
        assert intent.rationale is None
        assert intent.constraints is None
        assert intent.superseded_by is None
        assert intent.evidence_tests == []
        assert intent.supporting_docs == []
        assert intent.code_home == []
        assert intent.named_scopes == []
