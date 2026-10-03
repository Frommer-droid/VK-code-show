import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Build_Tools"))
from runtime_dll_policy import minimal_path, qt_runtime, validate_origins


class BuildPolicyTests(unittest.TestCase):
    def test_foreign_runtime_cannot_be_hidden_by_replacement(self):
        root = Path(__file__).resolve().parents[1]
        with self.assertRaisesRegex(RuntimeError, "Untrusted native origin"):
            qt_runtime(
                [("vcruntime140.dll", "C:/foreign/runtime/vcruntime140.dll", "BINARY")],
                root,
            )

    def test_sibling_of_project_is_not_trusted(self):
        root = Path(__file__).resolve().parents[1]
        source = root.parent / (root.name + "-foreign") / "native.dll"
        with self.assertRaises(RuntimeError):
            validate_origins([("native.dll", str(source), "BINARY")], root)

    def test_path_does_not_inherit_toolchain_directories(self):
        old = os.environ["PATH"]
        try:
            os.environ["PATH"] = "C:/foreign/toolchain"
            self.assertNotIn("foreign", minimal_path())
        finally:
            os.environ["PATH"] = old
