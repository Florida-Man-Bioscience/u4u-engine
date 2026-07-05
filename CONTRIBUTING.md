# Contributing

The annotation pipeline (`engine/pipeline.py` and the annotators it drives) is a pure Python function — bytes in, a result `dict` out. Keep that core path free of servers, databases, and web frameworks; PRs that add I/O, network servers, or a web framework to the annotation pipeline will be closed.

This rule scopes the *pipeline*, not all of `engine/`. Service modules under `engine/` — `engine/tracking/`, `engine/healthkit/`, `engine/users/` — deliberately own their FastAPI routers (`api.py`) and their Postgres/SQLite storage (`db.py`). That boundary is intentional: the pure pipeline stays pure, while the service layers around it may hold state and expose endpoints.

## Setup

```bash
pip install -e "./engine[vcf]"
pip install pytest responses
```

## Tests

```bash
pytest tests/ -v
```

All need to pass. If you're adding behavior, test it.

## Opening a PR

One change per PR. The description should explain what changed and why — not list every file you touched. If you're changing behavior that the specs describe, update the spec in the same PR.

`docs/` is the source of truth for intended behavior. If code and spec disagree, fix whichever is wrong and write it down.
