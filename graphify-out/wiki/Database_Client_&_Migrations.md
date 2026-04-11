# Database Client & Migrations

> 38 nodes

## Key Concepts

- **client.ts** (56 connections) — `paperclip/packages/db/src/client.ts`
- **reconcilePendingMigrationHistory()** (11 connections) — `paperclip/packages/db/src/client.ts`
- **applyPendingMigrationsManually()** (10 connections) — `paperclip/packages/db/src/client.ts`
- **createUtilitySql()** (7 connections) — `paperclip/packages/db/src/client.ts`
- **quoteIdentifier()** (7 connections) — `paperclip/packages/db/src/client.ts`
- **loadAppliedMigrations()** (7 connections) — `paperclip/packages/db/src/client.ts`
- **inspectMigrations()** (7 connections) — `paperclip/packages/db/src/client.ts`
- **listJournalMigrationEntries()** (6 connections) — `paperclip/packages/db/src/client.ts`
- **migrationStatementAlreadyApplied()** (6 connections) — `paperclip/packages/db/src/client.ts`
- **quoteLiteral()** (5 connections) — `paperclip/packages/db/src/client.ts`
- **ensureMigrationJournalTable()** (5 connections) — `paperclip/packages/db/src/client.ts`
- **recordMigrationHistoryEntry()** (5 connections) — `paperclip/packages/db/src/client.ts`
- **getMigrationTableColumnNames()** (5 connections) — `paperclip/packages/db/src/client.ts`
- **discoverMigrationTableSchema()** (5 connections) — `paperclip/packages/db/src/client.ts`
- **applyPendingMigrations()** (5 connections) — `paperclip/packages/db/src/client.ts`
- **migrationContentAlreadyApplied()** (4 connections) — `paperclip/packages/db/src/client.ts`
- **listJournalMigrationFiles()** (3 connections) — `paperclip/packages/db/src/client.ts`
- **readMigrationFileContent()** (3 connections) — `paperclip/packages/db/src/client.ts`
- **orderMigrationsByJournal()** (3 connections) — `paperclip/packages/db/src/client.ts`
- **migrationHistoryEntryExists()** (3 connections) — `paperclip/packages/db/src/client.ts`
- **migratePostgresIfEmpty()** (3 connections) — `paperclip/packages/db/src/client.ts`
- **sidebarBadges.ts** (2 connections) — `paperclip/ui/src/api/sidebarBadges.ts`
- **ApiError** (2 connections) — `paperclip/ui/src/api/client.ts`
- **isSafeIdentifier()** (2 connections) — `paperclip/packages/db/src/client.ts`
- **splitMigrationStatements()** (2 connections) — `paperclip/packages/db/src/client.ts`
- *... and 13 more nodes in this community*

## Relationships

- [[Paperclip UI Components]] (17 shared connections)
- [[Plugin Bridge System]] (2 shared connections)
- [[Issue Documents Section]] (1 shared connections)
- [[Access & Onboarding]] (1 shared connections)

## Source Files

- `paperclip/packages/db/src/client.ts`
- `paperclip/ui/src/api/client.ts`
- `paperclip/ui/src/api/sidebarBadges.ts`

## Audit Trail

- EXTRACTED: 197 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*