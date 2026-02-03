"""Tests for bootstrap model and tools."""

import tempfile
from pathlib import Path

from intention_audit.models.bootstrap import (
    BootstrapResult,
    BootstrapStage,
    CommitCluster,
    ImplementationRequirement,
    SynthesizedIntention,
)
from mcp_servers.intention_audit.tools.cluster_commits import cluster_commits
from mcp_servers.intention_audit.tools.extract_implementation_requirements import (
    extract_implementation_requirements,
)
from mcp_servers.intention_audit.tools.synthesize_user_requirements import (
    synthesize_user_requirements,
)
from mcp_servers.intention_audit.tools.verify_intention_tree import verify_intention_tree


class TestCommitCluster:
    """Tests for CommitCluster dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating CommitCluster from minimal dict."""
        data: dict = {
            "cluster_id": "CLUSTER-001",
            "commits": ["abc123", "def456"],
            "semantic_label": "Add user authentication",
        }
        cluster = CommitCluster.from_dict(data)

        assert cluster.cluster_id == "CLUSTER-001"
        assert len(cluster.commits) == 2
        assert cluster.semantic_label == "Add user authentication"
        assert cluster.confidence == 0.6  # default

    def test_from_dict_full(self) -> None:
        """Test creating CommitCluster with all fields."""
        data: dict = {
            "cluster_id": "CLUSTER-001",
            "commits": ["abc123"],
            "semantic_label": "Add login feature",
            "conventional_prefix": "feat",
            "confidence": 0.85,
            "files_touched": ["src/auth/login.py"],
        }
        cluster = CommitCluster.from_dict(data)

        assert cluster.conventional_prefix == "feat"
        assert cluster.confidence == 0.85
        assert len(cluster.files_touched) == 1

    def test_to_dict(self) -> None:
        """Test serializing CommitCluster to dict."""
        cluster = CommitCluster(
            cluster_id="CLUSTER-002",
            commits=["ghi789"],
            semantic_label="Fix bug",
            confidence=0.7,
        )
        result = cluster.to_dict()

        assert result["cluster_id"] == "CLUSTER-002"
        assert result["confidence"] == 0.7


class TestImplementationRequirement:
    """Tests for ImplementationRequirement dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating ImplementationRequirement from minimal dict."""
        data: dict = {
            "ir_id": "IR-001",
            "cluster_id": "CLUSTER-001",
            "description": "Implemented login validation",
        }
        ir = ImplementationRequirement.from_dict(data)

        assert ir.ir_id == "IR-001"
        assert ir.cluster_id == "CLUSTER-001"
        assert ir.description == "Implemented login validation"

    def test_from_dict_full(self) -> None:
        """Test creating ImplementationRequirement with all fields."""
        data: dict = {
            "ir_id": "IR-001",
            "cluster_id": "CLUSTER-001",
            "description": "Implemented login validation",
            "functions_modified": ["validate_credentials"],
            "classes_modified": ["User"],
            "tests_added": ["test_login"],
            "patterns_detected": ["input_validation"],
            "confidence": 0.8,
        }
        ir = ImplementationRequirement.from_dict(data)

        assert len(ir.functions_modified) == 1
        assert len(ir.patterns_detected) == 1
        assert ir.confidence == 0.8

    def test_to_dict(self) -> None:
        """Test serializing ImplementationRequirement to dict."""
        ir = ImplementationRequirement(
            ir_id="IR-002",
            cluster_id="CLUSTER-002",
            description="Fixed session bug",
            confidence=0.75,
        )
        result = ir.to_dict()

        assert result["ir_id"] == "IR-002"
        assert result["confidence"] == 0.75


class TestSynthesizedIntention:
    """Tests for SynthesizedIntention dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating SynthesizedIntention from minimal dict."""
        data: dict = {
            "intent_id": "INT-MINED-001",
            "title": "User Authentication",
            "type": "goal",
        }
        intention = SynthesizedIntention.from_dict(data)

        assert intention.intent_id == "INT-MINED-001"
        assert intention.title == "User Authentication"
        assert intention.type == "goal"
        assert intention.source == "mined"

    def test_from_dict_full(self) -> None:
        """Test creating SynthesizedIntention with all fields."""
        data: dict = {
            "intent_id": "INT-MINED-002",
            "title": "Login Flow",
            "description": "Handle user login",
            "type": "functionality",
            "source_ir_ids": ["IR-001"],
            "source_clusters": ["CLUSTER-001"],
            "parent_id": "INT-MINED-001",
            "child_ids": ["INT-MINED-003"],
            "code_home": ["src/auth/login.py"],
            "evidence_tests": ["tests/test_auth.py"],
            "source": "mined",
            "confidence": 0.75,
        }
        intention = SynthesizedIntention.from_dict(data)

        assert intention.parent_id == "INT-MINED-001"
        assert len(intention.child_ids) == 1
        assert intention.confidence == 0.75

    def test_to_dict(self) -> None:
        """Test serializing SynthesizedIntention to dict."""
        intention = SynthesizedIntention(
            intent_id="INT-MINED-003",
            title="Email Validation",
            description="Validate email format",
            type="implementation",
            confidence=0.85,
        )
        result = intention.to_dict()

        assert result["intent_id"] == "INT-MINED-003"
        assert result["source"] == "mined"


class TestBootstrapResult:
    """Tests for BootstrapResult dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating BootstrapResult from minimal dict."""
        data: dict = {
            "stage": "clustering",
            "success": True,
        }
        result = BootstrapResult.from_dict(data)

        assert result.stage == BootstrapStage.CLUSTERING
        assert result.success is True
        assert result.clusters == []

    def test_from_dict_full(self) -> None:
        """Test creating BootstrapResult with all artifacts."""
        data: dict = {
            "stage": "complete",
            "success": True,
            "clusters": [
                {
                    "cluster_id": "CLUSTER-001",
                    "commits": ["abc123"],
                    "semantic_label": "Auth feature",
                }
            ],
            "implementation_requirements": [
                {
                    "ir_id": "IR-001",
                    "cluster_id": "CLUSTER-001",
                    "description": "Login impl",
                }
            ],
            "synthesized_intentions": [
                {
                    "intent_id": "INT-001",
                    "title": "Auth",
                    "type": "goal",
                }
            ],
            "commits_analyzed": 50,
            "clusters_created": 5,
            "irs_extracted": 8,
            "intentions_synthesized": 10,
        }
        result = BootstrapResult.from_dict(data)

        assert result.stage == BootstrapStage.COMPLETE
        assert len(result.clusters) == 1
        assert len(result.implementation_requirements) == 1
        assert len(result.synthesized_intentions) == 1
        assert result.commits_analyzed == 50

    def test_is_complete(self) -> None:
        """Test is_complete method."""
        incomplete = BootstrapResult(stage=BootstrapStage.CLUSTERING, success=True)
        complete_success = BootstrapResult(stage=BootstrapStage.COMPLETE, success=True)
        complete_fail = BootstrapResult(stage=BootstrapStage.COMPLETE, success=False)

        assert incomplete.is_complete() is False
        assert complete_success.is_complete() is True
        assert complete_fail.is_complete() is False

    def test_get_low_confidence_intentions(self) -> None:
        """Test getting low confidence intentions."""
        high = SynthesizedIntention(
            intent_id="INT-001",
            title="High",
            description="",
            type="goal",
            confidence=0.8,
        )
        low = SynthesizedIntention(
            intent_id="INT-002",
            title="Low",
            description="",
            type="goal",
            confidence=0.3,
        )

        result = BootstrapResult(
            stage=BootstrapStage.COMPLETE,
            success=True,
            synthesized_intentions=[high, low],
        )

        low_confidence = result.get_low_confidence_intentions(threshold=0.5)
        assert len(low_confidence) == 1
        assert low_confidence[0].intent_id == "INT-002"


class TestClusterCommits:
    """Tests for cluster_commits MCP tool."""

    def test_valid_minimal(self) -> None:
        """Test saving minimal cluster data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            clusters_data: dict = {
                "clusters": [
                    {
                        "cluster_id": "CLUSTER-001",
                        "commits": ["abc123"],
                        "semantic_label": "Test cluster",
                    }
                ],
            }

            result = cluster_commits(cwd=tmpdir, clusters_data=clusters_data)

            assert result["success"] is True
            assert result["cluster_count"] == 1
            assert Path(result["path"]).exists()

    def test_missing_clusters(self) -> None:
        """Test that missing clusters field causes error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            clusters_data: dict = {"commits_analyzed": 10}

            result = cluster_commits(cwd=tmpdir, clusters_data=clusters_data)

            assert result["success"] is False
            assert "clusters" in result["error"]

    def test_invalid_confidence(self) -> None:
        """Test that invalid confidence causes error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            clusters_data: dict = {
                "clusters": [
                    {
                        "cluster_id": "CLUSTER-001",
                        "commits": ["abc123"],
                        "semantic_label": "Test",
                        "confidence": 1.5,  # Invalid: > 1.0
                    }
                ],
            }

            result = cluster_commits(cwd=tmpdir, clusters_data=clusters_data)

            assert result["success"] is False
            assert "confidence" in result["error"]


class TestExtractImplementationRequirements:
    """Tests for extract_implementation_requirements MCP tool."""

    def test_valid_minimal(self) -> None:
        """Test saving minimal requirements data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            requirements_data: dict = {
                "requirements": [
                    {
                        "ir_id": "IR-001",
                        "cluster_id": "CLUSTER-001",
                        "description": "Test requirement",
                    }
                ],
            }

            result = extract_implementation_requirements(
                cwd=tmpdir, requirements_data=requirements_data
            )

            assert result["success"] is True
            assert result["ir_count"] == 1

    def test_missing_required_field(self) -> None:
        """Test that missing required field causes error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            requirements_data: dict = {
                "requirements": [
                    {
                        "ir_id": "IR-001",
                        # Missing cluster_id and description
                    }
                ],
            }

            result = extract_implementation_requirements(
                cwd=tmpdir, requirements_data=requirements_data
            )

            assert result["success"] is False
            assert "cluster_id" in result["error"]


class TestSynthesizeUserRequirements:
    """Tests for synthesize_user_requirements MCP tool."""

    def test_valid_minimal(self) -> None:
        """Test saving minimal intentions data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            intentions_data: dict = {
                "intentions": [
                    {
                        "intent_id": "INT-001",
                        "title": "Test Goal",
                        "type": "goal",
                    }
                ],
            }

            result = synthesize_user_requirements(cwd=tmpdir, intentions_data=intentions_data)

            assert result["success"] is True
            assert result["intention_count"] == 1
            assert result["goal_count"] == 1

    def test_invalid_type(self) -> None:
        """Test that invalid intention type causes error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            intentions_data: dict = {
                "intentions": [
                    {
                        "intent_id": "INT-001",
                        "title": "Test",
                        "type": "invalid_type",
                    }
                ],
            }

            result = synthesize_user_requirements(cwd=tmpdir, intentions_data=intentions_data)

            assert result["success"] is False
            assert "type" in result["error"]


class TestVerifyIntentionTree:
    """Tests for verify_intention_tree MCP tool."""

    def test_valid_minimal(self) -> None:
        """Test saving minimal verified data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            verified_data: dict = {
                "intentions": [
                    {
                        "intent_id": "INT-001",
                        "title": "Verified Goal",
                        "type": "goal",
                    }
                ],
            }

            result = verify_intention_tree(cwd=tmpdir, verified_data=verified_data)

            assert result["success"] is True
            assert result["intention_count"] == 1
            assert result["linked_tests"] == 0

    def test_with_evidence_mappings(self) -> None:
        """Test saving verified data with evidence mappings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            verified_data: dict = {
                "intentions": [
                    {
                        "intent_id": "INT-001",
                        "title": "Verified Goal",
                        "type": "goal",
                    }
                ],
                "evidence_mappings": [
                    {
                        "intent_id": "INT-001",
                        "test_path": "tests/test_goal.py::test_it",
                    }
                ],
            }

            result = verify_intention_tree(cwd=tmpdir, verified_data=verified_data)

            assert result["success"] is True
            assert result["linked_tests"] == 1
