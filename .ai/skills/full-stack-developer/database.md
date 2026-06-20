# Data Layer Playbook

Reference for choosing, modeling, and operating the data layer. Load when
designing schemas, writing queries, or reviewing data access.

## Choose the store for the access pattern

| Need | Choose | Why |
|------|--------|-----|
| Related entities, transactions, ad-hoc queries (most apps) | **Relational (PostgreSQL)** | Integrity, joins, ACID, mature tooling |
| Local/embedded, single-writer | **SQLite** | Zero-ops; great for dev and small apps |
| Genuinely document-shaped, flexible/evolving schema, high write volume | **Document (MongoDB)** | Schema flexibility, horizontal scale |
| Caching, sessions, rate limits, queues | **Key-value (Redis)** | In-memory speed, TTLs |
| Full-text / fuzzy search | **Search engine (Elastic/OpenSearch, pg full-text)** | Relevance ranking |

**Default to PostgreSQL.** Pick NoSQL because the access pattern truly fits, not
because "schemas are annoying." A document store does not remove the need to
model — it moves the modeling into your query design.

## Relational modeling

- **Normalize first** (3NF) to remove duplication; denormalize **deliberately**
  for a measured read-performance need, with a plan to keep copies consistent.
- Every table has a primary key. Use foreign keys + constraints — let the database
  enforce integrity, don't rely on application code alone.
- Pick correct types (`timestamptz` not strings for time; `numeric` not float for
  money; enums/check constraints for fixed sets).
- Model relationships explicitly: 1-to-many via FK, many-to-many via a join table.

## NoSQL (document) modeling

- Model around **how you read.** Embed data that is read together and owned by the
  parent; reference data that is shared, large, or independently updated.
- Embedding favors read performance; referencing favors normalization and
  avoiding unbounded document growth. Watch the document size limit.
- You still need indexes and a consistency story; "schemaless" means *you* own the
  schema in code (validation at the boundary).

## Indexing & query performance

- Index columns used in `WHERE`, `JOIN`, `ORDER BY`, and foreign keys — but index
  for real query patterns; every index slows writes and costs storage.
- **Read query plans** (`EXPLAIN ANALYZE`) before and after; don't guess.
- **Kill N+1 queries** — the #1 ORM performance bug. Eager-load:
  - Django: `select_related` (FK/1-1 join) / `prefetch_related` (many).
  - SQLAlchemy: `joinedload` / `selectinload`.
  - Prisma/TypeORM: `include` / relations.
- Select only needed columns; paginate (prefer keyset/cursor for large sets over
  large `OFFSET`).
- Cache expensive reads in Redis **with an explicit invalidation strategy** — a
  cache without an invalidation plan is a correctness bug in waiting.

## ORM vs raw SQL

- ORM by default (Django ORM, SQLAlchemy, Prisma, TypeORM): safe, productive,
  parameterized.
- Drop to raw/SQL builder for complex analytical queries the ORM expresses poorly
  — still **parameterized**, never string-concatenated (SQL injection).
- Know what SQL your ORM emits on hot paths; ORMs hide cost.

## Migrations

- All schema changes go through migration tooling (Django migrations, Alembic,
  Prisma Migrate, Flyway). The migration history is the schema's source of truth.
- Review the generated migration before applying; never hand-edit an applied one —
  add a new migration to fix forward.
- Design for **zero-downtime**: expand → migrate data → contract. Add nullable
  columns / new tables first; backfill; switch reads/writes; remove the old shape
  later. Avoid destructive changes in the same deploy that depends on them.
- Migrations must be reversible or have a documented recovery path. Test on a copy
  of production-like data.

## Transactions & integrity

- Wrap multi-step writes that must succeed-or-fail-together in a transaction.
- Understand isolation levels and the locking your DB uses; keep transactions
  short to avoid contention.
- Enforce invariants with DB constraints (unique, FK, check) in addition to app
  validation — defense in depth.

## Operations

- **Backups** with tested restores (an untested backup is a hope, not a backup).
- Least-privilege DB users per service; never the superuser from the app.
- Connection pooling (PgBouncer, ORM pool) under concurrency.
- Encrypt in transit (TLS) and at rest for sensitive data; never log raw
  credentials or PII.

## Review checklist

- [ ] Store choice justified by the actual access pattern
- [ ] Keys, foreign keys, and constraints present; correct column types
- [ ] Indexes match real query patterns; no unindexed hot lookups
- [ ] No N+1; queries paginated; only needed columns selected
- [ ] Parameterized queries/ORM only — no string-built SQL
- [ ] Schema changes via reviewed, reversible migrations
- [ ] Multi-step writes are transactional; invariants enforced in the DB
- [ ] Backups + least-privilege credentials in place
