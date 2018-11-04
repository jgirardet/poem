from fixtures import poetry, PoetryTestCase, PoetryDeferredTestCase
import os
from pathlib import Path
import sublime
import time
import toml


class TestInstall(PoetryDeferredTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.view.erase_status(poetry.PACKAGE_NAME)
        self.result = None

    def tearDown(self):
        self.view.erase_status(poetry.PACKAGE_NAME)

    def test_set_python_interpreter(self):
        self.window.run_command("poetry_set_python_interpreter")
        project_data = self.window.project_data()

        if (
            "TRAVIS" in os.environ and os.environ["TRAVIS_OS_NAME"] == "linux"
        ):  # because poetry ignore .venv ifVIRTUAL_ENV set
            base = Path(os.environ["VIRTUAL_ENV"]).resolve()
        else:
            base = self.venv.resolve()
        self.assertEqual(
            project_data,
            {
                "settings": {"python_interpreter": str(base / "bin" / "python")},
                "folders": [{"path": self.dir.name}],
            },
        )

    def status(self):

        if "succes" in self.view.get_status("poetry"):
            self.result = True
            return True

        if "fail" in self.view.get_status("poetry"):
            self.result = False
            return True

    def test_install(self):

        self.window.run_command("poetry_install")
        yield self.status
        self.assertEqual(self.result, True)
        (self.dirpath / "poetry.lock").unlink()

    def test_install_no_dev(self):
        self.window.run_command("poetry_install_no_dev")

        yield self.status

        self.assertTrue((self.dirpath / "poetry.lock").exists())
        self.assertEqual(self.result, True)
        (self.dirpath / "poetry.lock").unlink()

    def assert_in_toml(self, content, section="dependencies"):
        toml_content = toml.loads(self.pyproject.read_text())
        section = "dev-dependencies" if section == "dev" else section
        self.assertIn(content, toml_content["tool"]["poetry"][section])

    def assert_not_in_toml(self, content, section="dependencies"):
        toml_content = toml.loads(self.pyproject.read_text())
        section = "dev-dependencies" if section == "dev" else section
        self.assertNotIn(content, toml_content["tool"]["poetry"][section])

    def test_add(self):

        self.window.run_command("poetry_add", args={"custom": "toml"})
        yield self.status
        self.assert_in_toml("toml")

    def test_add_dev(self):

        self.window.run_command("poetry_add_dev", args={"custom": "tomlkit"})
        yield self.status
        self.assert_in_toml("tomlkit", "dev")


# # class TestAddRemovePackage(PoetryDeferredTestCase)
#     @patch(poetry.commands.PoetryCommand.window.show_input_panel)
#     def test_add(self):

#         self.window.run_command("poetry_add")
#         yield self.status
#         self.assertTrue((self.dirpath / "poetry.lock").exists())
#         self.assertEqual(self.result, True)
#         (self.dirpath / "poetry.lock").unlink()
