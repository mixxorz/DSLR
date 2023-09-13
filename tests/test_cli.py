import os
from datetime import datetime
from itertools import product
from typing import Any, List, Tuple
from unittest import TestCase, mock
from urllib.parse import quote

from click.testing import CliRunner

from dslr import cli, operations, runner


def stub_exec_shell(*args, **kwargs) -> runner.Result:
    return runner.Result(stdout="", stderr="")


def stub_exec_sql(*args, **kwargs) -> List[Tuple[Any, ...]]:
    fake_snapshot_1 = operations.generate_snapshot_db_name(
        "existing-snapshot-1",
        created_at=datetime(2020, 1, 1, 0, 0, 0, 0),
    )
    fake_snapshot_2 = operations.generate_snapshot_db_name(
        "existing-snapshot-2",
        created_at=datetime(2020, 1, 2, 0, 0, 0, 0),
    )
    return [(fake_snapshot_1, "100 kB"), (fake_snapshot_2, "100 kB")]


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

    def test_snapshot_overwrite_with_yes(self):
        # stub_exec sets up a fake snapshot called "existing-snapshot-1"
        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["snapshot", "existing-snapshot-1", "-y"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertNotIn(
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

    def test_rename_overwrite_with_yes(self):
        runner = CliRunner()
        result = runner.invoke(
            cli.cli, ["rename", "existing-snapshot-1", "existing-snapshot-2", "-y"]
        )

        self.assertEqual(result.exit_code, 0)
        self.assertNotIn(
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

    def test_import_overwrite_with_yes(self):
        runner = CliRunner()
        result = runner.invoke(
            cli.cli, ["import", "pyproject.toml", "existing-snapshot-1", "-y"]
        )

        self.assertEqual(result.exit_code, 0)
        self.assertNotIn(
            "Snapshot existing-snapshot-1 already exists. Overwrite?", result.output
        )
        self.assertIn(
            "Imported snapshot existing-snapshot-1 from pyproject.toml",
            result.output,
        )


@mock.patch("dslr.cli.get_snapshots")
class ConfigTest(TestCase):
    @mock.patch.dict(
        os.environ, {"DATABASE_URL": "postgres://envvar:pw@test:5432/my_db"}
    )
    @mock.patch("dslr.cli.settings")
    def test_database_url(self, mock_cli_settings, mock_get_snapshots):
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["list"])

        self.assertEqual(result.exit_code, 0)

        mock_cli_settings.initialize.assert_called_once_with(
            debug=False,
            url="postgres://envvar:pw@test:5432/my_db",
        )

    @mock.patch("dslr.cli.settings")
    def test_toml(self, mock_cli_settings, mock_get_snapshots):
        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=b"url = 'postgres://toml:pw@test:5432/my_db'"),
        ):
            runner = CliRunner()
            result = runner.invoke(cli.cli, ["list"])

        self.assertEqual(result.exit_code, 0)

        mock_cli_settings.initialize.assert_called_once_with(
            debug=False,
            url="postgres://toml:pw@test:5432/my_db",
        )

    @mock.patch("dslr.cli.settings")
    def test_db_option(self, mock_cli_settings, mock_get_snapshots):
        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--url", "postgres://cli:pw@test:5432/my_db", "list"],
        )

        self.assertEqual(result.exit_code, 0)

        mock_cli_settings.initialize.assert_called_once_with(
            debug=False,
            url="postgres://cli:pw@test:5432/my_db",
        )

    @mock.patch("dslr.cli.settings")
    def test_settings_preference_order(self, mock_cli_settings, mock_get_snapshots):
        # No options passed (e.g. PG environment variables are used)
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["list"])
        self.assertEqual(result.exit_code, 0)

        # DATABASE_URL environment variable is used
        with mock.patch.dict(
            os.environ, {"DATABASE_URL": "postgres://envvar:pw@test:5432/my_db"}
        ):
            runner = CliRunner()
            result = runner.invoke(cli.cli, ["list"])
            self.assertEqual(result.exit_code, 0)

            # TOML file is used
            with mock.patch(
                "builtins.open",
                mock.mock_open(read_data=b"url = 'postgres://toml:pw@test:5432/my_db'"),
            ):
                runner = CliRunner()
                result = runner.invoke(cli.cli, ["list"])
                self.assertEqual(result.exit_code, 0)

                # --url option is used
                runner = CliRunner()
                result = runner.invoke(
                    cli.cli,
                    ["--url", "postgres://cli:pw@test:5432/my_db", "list"],
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

    @mock.patch("dslr.config.DatabaseConnection")
    def test_encoded_username_password(
        self, mock_database_connection, mock_get_snapshots
    ):
        usernames = ["user", "user@example.com"]
        passwords = ["pw", "f4A$#%&?!_@:asvb"]

        for username, password in product(usernames, passwords):
            with self.subTest(username=username, password=password):
                mock_database_connection.reset_mock()

                username_encoded = quote(username)
                password_encoded = quote(password)

                # DATABASE_URL environment variable is used
                with mock.patch.dict(
                    os.environ,
                    {
                        "DATABASE_URL": (
                            f"postgres://{username_encoded}:{password_encoded}"
                            "@test:5432/my_db"
                        )
                    },
                ):
                    runner = CliRunner()
                    result = runner.invoke(cli.cli, ["list"])

                    self.assertEqual(result.exit_code, 0)

                    self.assertEqual(1, mock_database_connection.call_count)
                    self.assertEqual(
                        mock_database_connection.call_args.kwargs["username"], username
                    )
                    self.assertEqual(
                        mock_database_connection.call_args.kwargs["password"], password
                    )
