import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from proguard_to_tiny import convert, parse_mapping


SAMPLE = """# synthetic fixture; no Minecraft mapping data
net.minecraft.Example -> a:
    int count -> b
    java.lang.String name -> c
    1:2:void <init>():3:4 -> <init>
    5:8:net.minecraft.Other find(net.minecraft.Other,int[]):9:12 -> d
net.minecraft.Other -> b:
    boolean ready -> a
"""


class ProguardToTinyTests(unittest.TestCase):
    def test_converts_classes_fields_and_methods(self):
        tiny = convert(SAMPLE)
        self.assertIn("tiny\t2\t0\tofficial\tnamed", tiny)
        self.assertIn("c\ta\tnet/minecraft/Example", tiny)
        self.assertIn("\tf\tI\tb\tcount", tiny)
        self.assertIn("\tf\tLjava/lang/String;\tc\tname", tiny)
        self.assertIn("\tm\t()V\t<init>\t<init>", tiny)
        self.assertIn(
            "\tm\t(Lb;[I)Lb;\td\tfind", tiny
        )
        self.assertIn("c\tb\tnet/minecraft/Other", tiny)

    def test_class_order_is_deterministic(self):
        self.assertEqual(convert(SAMPLE), convert(SAMPLE))

    def test_rejects_empty_mapping(self):
        with self.assertRaises(ValueError):
            parse_mapping("# no class entries\n")

    def test_rejects_void_arrays(self):
        with self.assertRaises(ValueError):
            convert("example.Test -> a:\n    void[] bad -> b\n")


if __name__ == "__main__":
    unittest.main()
