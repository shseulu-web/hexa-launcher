import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.prepare_1_21_10 import extract_data_resources


class VanillaDataResourceTests(unittest.TestCase):
    def test_extracts_json_and_reports_namespaces_and_categories(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            jar = root / "server.jar"
            destination = root / "data" / "server"
            with zipfile.ZipFile(jar, "w") as archive:
                archive.writestr("data/minecraft/tags/blocks/mineable/pickaxe.json",
                                 json.dumps({"replace": False, "values": ["minecraft:stone"]}))
                archive.writestr("data/example/worldgen/biome/test.json",
                                 json.dumps({"temperature": 0.8}))
                archive.writestr("assets/minecraft/lang/en_us.json", "{}")
            report = extract_data_resources(jar, destination)
            self.assertEqual(report["resource_count"], 2)
            self.assertEqual(report["namespace_counts"], {"minecraft": 1, "example": 1})
            self.assertEqual(report["category_counts"], {"tags": 1, "worldgen": 1})
            self.assertTrue((destination / "data/minecraft/tags/blocks/mineable/pickaxe.json").is_file())

    def test_rejects_unsafe_paths_and_cleans_partial_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            jar = root / "server.jar"
            destination = root / "data"
            with zipfile.ZipFile(jar, "w") as archive:
                archive.writestr("data/../../outside.json", "{}")
            with self.assertRaisesRegex(ValueError, "Unsafe data resource path"):
                extract_data_resources(jar, destination)
            self.assertFalse(destination.exists())
            self.assertFalse((root / "outside.json").exists())

    def test_rejects_invalid_json_and_cleans_partial_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            jar = root / "server.jar"
            destination = root / "data"
            with zipfile.ZipFile(jar, "w") as archive:
                archive.writestr("data/minecraft/tags/blocks/bad.json", "{not-json")
            with self.assertRaises(json.JSONDecodeError):
                extract_data_resources(jar, destination)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
