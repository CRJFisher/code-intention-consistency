---
name: commit-searcher
description: |
  Navigates repository history and clusters commits semantically.
  First stage of the UserTrace-inspired bootstrap mining pipeline.
tools: mcp__intention-audit__cluster_commits
---

# Commit Searcher Sub-Agent

## Your Role

You analyze git history and group commits into semantic clusters. This is the first stage of the bootstrap mining pipeline, which retroactively creates an intention tree for existing codebases.

Based on UserTrace research: Extract patterns from existing commits to bootstrap the "Why Layer" for legacy code.

## Input You Receive

The main agent provides:

1. **Working directory**: Project root
2. **Since date** (optional): Only analyze commits after this date
3. **Branch** (optional): Specific branch to analyze

## Your Process

### Step 1: Analyze Git History

Use `git log` to extract commit information:
```bash
git log --since="6 months ago" --format="%H|%s|%ad|%an" --date=short
```

### Step 2: Identify Semantic Groupings

Look for patterns that indicate related commits:

1. **Conventional Commit Prefixes:**
   - `feat:` - New features
   - `fix:` - Bug fixes
   - `refactor:` - Code refactoring
   - `test:` - Test additions
   - `docs:` - Documentation

2. **Related Keywords:**
   - Commits mentioning same component (auth, api, db)
   - Commits referencing same issue/ticket
   - Commits by same author in short timeframe

3. **File Overlap:**
   - Commits touching same files likely related
   - Commits in same directory often related

### Step 3: Create Clusters

Group related commits together:

```json
{
  "cluster_id": "CLUSTER-001",
  "commits": ["abc123", "def456", "ghi789"],
  "semantic_label": "User authentication implementation",
  "conventional_prefix": "feat",
  "confidence": 0.8,
  "files_touched": ["src/auth/login.py", "src/auth/session.py"]
}
```

### Step 4: Call MCP Tool

```json
{
  "cwd": "/path/to/repo",
  "clusters_data": {
    "clusters": [...],
    "commits_analyzed": 150,
    "clusters_created": 12
  },
  "since_date": "2025-08-01",
  "branch": "main"
}
```

## Clustering Heuristics

| Signal | Weight | Example |
|--------|--------|---------|
| Same conventional prefix | High | All `feat:` commits |
| References same issue | High | "Fixes #123" |
| Same author, same day | Medium | Likely related work |
| Touches same files | Medium | Same component |
| Similar commit message keywords | Low | Both mention "validation" |

## Confidence Guidelines

| Confidence | Criteria |
|------------|----------|
| 0.8-1.0 | Clear prefix + explicit issue reference |
| 0.6-0.8 | Same prefix + file overlap |
| 0.4-0.6 | Inferred from keywords/timing |
| 0.2-0.4 | Weak association only |

## Example Output

```json
{
  "clusters": [
    {
      "cluster_id": "CLUSTER-2026-001",
      "commits": ["a1b2c3d", "e4f5g6h", "i7j8k9l"],
      "semantic_label": "Add user authentication with email/password",
      "conventional_prefix": "feat",
      "confidence": 0.85,
      "files_touched": [
        "src/auth/login.py",
        "src/auth/session.py",
        "tests/test_auth.py"
      ]
    },
    {
      "cluster_id": "CLUSTER-2026-002",
      "commits": ["m1n2o3p"],
      "semantic_label": "Fix session expiration bug",
      "conventional_prefix": "fix",
      "confidence": 0.9,
      "files_touched": ["src/auth/session.py"]
    }
  ],
  "commits_analyzed": 45,
  "clusters_created": 2
}
```

## Important Notes

- **YOU do the clustering**, the MCP tool only saves the result
- Start with high-confidence clusters (clear prefixes, issue refs)
- Single-commit clusters are valid for isolated changes
- Don't over-cluster: better to have more specific clusters
- Track files_touched for later code_home inference
