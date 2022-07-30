import os
from unittest import TestCase, mock

from click.testing import CliRunner

from dslr import cli, operations, runner


def stub_exec(*cmd: str):
    # Pretend that there is a snapshot called "existing-snapshot"
    if "SELECT datname FROM pg_database" in cmd:
        fake_snapshot_db_name = operations.generate_snapshot_db_name(
            "existing-snapshot"
        )
        return runner.Result(returncode=0, stdout=fake_snapshot_db_name, stderr="")

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
        # stub_exec sets up a fake snapshot called "existing-snapshot"
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["snapshot", "existing-snapshot"], input="y\n")

        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "Snapshot existing-snapshot already exists. Overwrite?", result.output
        )
        self.assertIn("Updated snapshot existing-snapshot", result.output)
