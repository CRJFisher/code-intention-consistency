"""
Fixture conftest - prevents pytest from collecting sample repos as tests.
"""

collect_ignore_glob = ["sample_repos/**/*"]
