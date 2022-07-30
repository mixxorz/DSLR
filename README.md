<br />
<br />
<p align="center">
  <img width="281" height="84" src="https://user-images.githubusercontent.com/3102758/181914025-44bff27e-aac1-4d1b-a037-9fa98f9fed65.png">
</p>
<br />

<p align="center">
  <a href=""><img src="" alt=""></a>
  <a href="https://badge.fury.io/py/dslr"><img src="https://badge.fury.io/py/dslr.svg" alt="PyPI version"></a>
  <a href="https://pypi.python.org/pypi/dslr/"><img src="https://img.shields.io/pypi/pyversions/dslr.svg" alt="PyPI Supported Python Versions"></a>
  <a href="https://github.com/mixxorz/dslr"><img src="https://github.com/mixxorz/dslr/actions/workflows/tests.yml/badge.svg" alt="GitHub Actions (Code quality and tests)"></a>

</p>
<br />

---

Database Snapshot, List, and Restore

Take lightning fast snapshots of your local Postgres databases.

## What is this?

DSLR is a tool that allows you to quickly take and restore database snapshots
when you're writing database migrations, switching branches, or messing with
SQL.

It's meant to be a spiritual successor to
[Stellar](https://github.com/fastmonkeys/stellar).

**Important:** DSLR is intended for development use only. It is not advisable to
use DSLR on production databases.

## Performance

DSLR is really fast.

_Impressive chart goes here_

## Install

```
pip install DSLR
```

DSLR requires that the Postgres client binaries (`psql`, `createdb`, `dropdb`)
are present in your `PATH`. DSLR uses them to interact with Postgres.

## Usage

First you need to point DSLR to the database you want to take snapshots of. The
easiest way to do this is to export the `DATABASE_URL` environment variable.

```bash
export DATABASE_URL=postgres://username:password@host:port/database_name
```

Alternatively, you can pass the connection string via the `--db` option.

You're ready to use DSLR!

```
$ dslr snapshot my-first-snapshot
Created new snapshot my-first-snapshot

$ dslr restore my-first-snapshot
Restored database from snapshot my-first-snapshot

$ dslr list

  Name                Created
 ────────────────────────────────────
  my-first-snapshot   2 minutes ago

$ dslr rename my-first-snapshot fresh-db
Renamed snapshot my-first-snapshot to fresh-db

$ dslr delete some-old-snapshot
Deleted some-old-snapshot

$ dslr export my-feature-test
Exported snapshot my-feature-test to my-feature-test_20220730-075650.dump

$ dslr import snapshot-from-a-friend_20220730-080632.dump friend-snapshot
Imported snapshot friend-snapshot from snapshot-from-a-friend_20220730-080632.dump
```

## How does it work?

DSLR takes snapshots by cloning databases using Postgres' [Template
Databases](https://www.postgresql.org/docs/current/manage-ag-templatedbs.html)
functionality. This is the main source of DSLR's speed.

This means that taking a snapshot is just creating a new database using the main
database as the template. Restoring a snapshot is just deleting the main
database and creating a new database using the snapshot database as the
template. So on and so forth.

## License

MIT
