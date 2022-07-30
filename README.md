# DSLR

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

At this point, you're ready to take your first snapshot.

```
# Take a snapshot
$ dslr snapshot my-first-snapshot
Created new snapshot my-first-snapshot
```

## Documentation

```
$ dslr --help
Usage: dslr [OPTIONS] COMMAND [ARGS]...

Options:
  --db TEXT             The database connection string to the database you
                        want to take snapshots of. If not provided, DSLR will
                        try to read it from the DATABASE_URL environment
                        variable.

                        Example:
                        postgres://username:password@host:port/database_name
                        [required]
  --debug / --no-debug  Show additional debugging information.
  --help                Show this message and exit.

Commands:
  delete    Deletes a snapshot
  export    Exports a snapshot to a file
  import    Imports a snapshot from a file
  list      Shows a list of all snapshots
  rename    Renames a snapshot
  restore   Restores the database from a snapshot
  snapshot  Takes a snapshot of the database
```

## License

MIT
