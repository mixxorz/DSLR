import os
from datetime import datetime
from unittest import TestCase, mock

from click.testing import CliRunner

from dslr import cli, operations, runner


def stub_exec(*cmd: str):
    # Set up fake snapshots
    if "SELECT datname FROM pg_database" in cmd:
        fake_snapshot_1 = operations.generate_snapshot_db_name(
            "existing-snapshot-1",
            created_at=datetime(2020, 1, 1, 0, 0, 0, 0),
        )
        fake_snapshot_2 = operations.generate_snapshot_db_name(
            "existing-snapshot-2",
            created_at=datetime(2020, 1, 2, 0, 0, 0, 0),
        )
        return runner.Result(
            returncode=0,
            stdout="\n".join([fake_snapshot_1, fake_snapshot_2]),
            stderr="",
        )

    return runner.Result(returncode=0, stdout="", stderr="")


@mock.patch.dict(os.environ, {"DATABASE_URL": "postgres://user:pw@test:5432/my_db"})
@mock.patch("dslr.operations.exec", new=stub_exec)
class CliTest(TestCase):
    def test_executes(self):
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["--help"])

        self.assertEqual(result.exit_code, 0)

    def test_snapshot(self):
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["snapshot", "my-snapshot"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Created new snapshot my-snapshot", result.output)

    def test_snapshot_overwrite(self):
        # stub_exec sets up a fake snapshot called "existing-snapshot-1"
        runner = CliRunner()
        result = runner.invoke(
            cli.cli, ["snapshot", "existing-snapshot-1"], input="y\n"
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "Snapshot existing-snapshot-1 already exists. Overwrite?", result.output
        )
        self.assertIn("Updated snapshot existing-snapshot-1", result.output)

    def test_restore(self):
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["restore", "existing-snapshot-1"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "Restored database from snapshot existing-snapshot-1", result.output
        )

    def test_restore_not_found(self):
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["restore", "not-found"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Snapshot not-found does not exist", result.output)

    def test_list(self):
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["list"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("existing-snapshot-1", result.output)

    def test_delete(self):
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["delete", "existing-snapshot-1"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Deleted snapshot existing-snapshot-1", result.output)

    def test_delete_not_found(self):
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["delete", "not-found"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Snapshot not-found does not exist", result.output)

    def test_rename(self):
        runner = CliRunner()
        result = runner.invoke(
            cli.cli, ["rename", "existing-snapshot-1", "new-snapshot"]
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "Renamed snapshot existing-snapshot-1 to new-snapshot", result.output
        )

    def test_rename_overwrite(self):
        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["rename", "existing-snapshot-1", "existing-snapshot-2"],
            input="y\n",
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "Snapshot existing-snapshot-2 already exists. Overwrite?", result.output
        )
        self.assertIn(
            "Renamed snapshot existing-snapshot-1 to existing-snapshot-2", result.output
        )

    def test_export(self):
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["export", "existing-snapshot-1"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "Exported snapshot existing-snapshot-1 to "
            "existing-snapshot-1_20200101-000000.dump",
            result.output.replace("\n", ""),
        )

    def test_export_not_found(self):
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["export", "not-found"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Snapshot not-found does not exist", result.output)

    def test_import(self):
        runner = CliRunner()
        result = runner.invoke(
            cli.cli, ["import", "pyproject.toml", "imported-snapshot"]
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "Imported snapshot imported-snapshot from pyproject.toml",
            result.output,
        )

    def test_import_overwrite(self):
        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["import", "pyproject.toml", "existing-snapshot-1"],
            input="y\n",
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "Snapshot existing-snapshot-1 already exists. Overwrite?", result.output
        )
        self.assertIn(
            "Imported snapshot existing-snapshot-1 from pyproject.toml",
            result.output,
        )
