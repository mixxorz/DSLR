import os
from datetime import datetime
from typing import Any, List, Optional, Tuple
from unittest import TestCase, mock

from click.testing import CliRunner

from dslr import cli, operations, runner


def stub_exec_shell(*cmd: str):
    return runner.Result(returncode=0, stdout="", stderr="")


def stub_exec_sql(sql: str, data: Optional[List[Any]] = None) -> List[Tuple[Any, ...]]:
    fake_snapshot_1 = operations.generate_snapshot_db_name(
        "existing-snapshot-1",
        created_at=datetime(2020, 1, 1, 0, 0, 0, 0),
    )
    fake_snapshot_2 = operations.generate_snapshot_db_name(
        "existing-snapshot-2",
        created_at=datetime(2020, 1, 2, 0, 0, 0, 0),
    )
    return [(fake_snapshot_1,), (fake_snapshot_2,)]


@mock.patch.dict(os.environ, {"DATABASE_URL": "postgres://user:pw@test:5432/my_db"})
@mock.patch("dslr.operations.exec_shell", new=stub_exec_shell)
@mock.patch("dslr.operations.exec_sql", new=stub_exec_sql)
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


@mock.patch("dslr.operations.exec_shell", new=stub_exec_shell)
@mock.patch("dslr.operations.exec_sql", new=stub_exec_sql)
class ConfigTest(TestCase):
    @mock.patch.dict(
        os.environ, {"DATABASE_URL": "postgres://envvar:pw@test:5432/my_db"}
    )
    @mock.patch("dslr.cli.settings")
    @mock.patch("dslr.operations.settings")
    def test_database_url(self, mock_operations_settings, mock_cli_settings):
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["snapshot", "my-snapshot"])

        self.assertEqual(result.exit_code, 0)

        mock_cli_settings.initialize.assert_called_once_with(
            debug=False,
            url="postgres://envvar:pw@test:5432/my_db",
        )

    @mock.patch("dslr.cli.settings")
    @mock.patch("dslr.operations.settings")
    def test_toml(self, mock_operations_settings, mock_cli_settings):
        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=b"url = 'postgres://toml:pw@test:5432/my_db'"),
        ):
            runner = CliRunner()
            result = runner.invoke(cli.cli, ["snapshot", "my-snapshot"])

        self.assertEqual(result.exit_code, 0)

        mock_cli_settings.initialize.assert_called_once_with(
            debug=False,
            url="postgres://toml:pw@test:5432/my_db",
        )

    @mock.patch("dslr.cli.settings")
    @mock.patch("dslr.operations.settings")
    def test_db_option(self, mock_operations_settings, mock_cli_settings):
        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--url", "postgres://cli:pw@test:5432/my_db", "snapshot", "my-snapshot"],
        )

        self.assertEqual(result.exit_code, 0)

        mock_cli_settings.initialize.assert_called_once_with(
            debug=False,
            url="postgres://cli:pw@test:5432/my_db",
        )

    @mock.patch("dslr.cli.settings")
    @mock.patch("dslr.operations.settings")
    def test_settings_preference_order(
        self, mock_operations_settings, mock_cli_settings
    ):
        # No options passed (e.g. PG environment variables are used)
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["snapshot", "my-snapshot"])
        self.assertEqual(result.exit_code, 0)

        # DATABASE_URL environment variable is used
        with mock.patch.dict(
            os.environ, {"DATABASE_URL": "postgres://envvar:pw@test:5432/my_db"}
        ):
            runner = CliRunner()
            result = runner.invoke(cli.cli, ["snapshot", "my-snapshot"])
            self.assertEqual(result.exit_code, 0)

            # TOML file is used
            with mock.patch(
                "builtins.open",
                mock.mock_open(read_data=b"url = 'postgres://toml:pw@test:5432/my_db'"),
            ):
                runner = CliRunner()
                result = runner.invoke(cli.cli, ["snapshot", "my-snapshot"])
                self.assertEqual(result.exit_code, 0)

                # --url option is used
                runner = CliRunner()
                result = runner.invoke(
                    cli.cli,
                    [
                        "--url",
                        "postgres://cli:pw@test:5432/my_db",
                        "snapshot",
                        "my-snapshot",
                    ],
                )
                self.assertEqual(result.exit_code, 0)

        # Check that the correct order of settings is used
        self.assertEqual(4, mock_cli_settings.initialize.call_count)

        self.assertEqual(
            mock_cli_settings.initialize.call_args_list,
            [
                # Nothing is passed
                mock.call(debug=False, url=""),
                # DATABASE_URL is present so use that
                mock.call(debug=False, url="postgres://envvar:pw@test:5432/my_db"),
                # TOML is present, so use that over DATABASE_URL
                mock.call(debug=False, url="postgres://toml:pw@test:5432/my_db"),
                # --url is present, so use that over everything
                mock.call(debug=False, url="postgres://cli:pw@test:5432/my_db"),
            ],
        )
