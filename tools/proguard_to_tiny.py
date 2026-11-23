#!/usr/bin/env python3
"""Convert a local Mojang ProGuard mapping file into Tiny v2 (obfuscated -> named).

Mapping inputs and generated Tiny files are local development artifacts and must not
be committed or redistributed. This tool intentionally does not download game files.
"""

import argparse
import re
from pathlib import Path


CLASS_LINE = re.compile(r"^([^\s].*?)\s+->\s+([^\s:]+):$")
LINE_PREFIX = re.compile(r"^\d+:\d+:")
LINE_SUFFIX = re.compile(r":\d+:\d+$")
METHOD = re.compile(r"^(\S+)\s+(.+?)\((.*)\)$")


def internal(name):
    return name.replace(".", "/")


def java_type_descriptor(name, original_to_obfuscated):
    name = name.strip()
    dimensions = 0
    while name.endswith("[]"):
        dimensions += 1
        name = name[:-2].strip()
    primitives = {
        "void": "V", "boolean": "Z", "byte": "B", "char": "C",
        "short": "S", "int": "I", "long": "J", "float": "F", "double": "D",
    }
    if name not in primitives:
        mapped = original_to_obfuscated.get(name, name)
        descriptor = "L" + internal(mapped) + ";"
    else:
        descriptor = primitives[name]
    if descriptor == "V" and dimensions:
        raise ValueError("void[] is not a valid Java type")
    return "[" * dimensions + descriptor


def strip_line_numbers(value):
    value = LINE_PREFIX.sub("", value)
    return LINE_SUFFIX.sub("", value)


def parse_mapping(text):
    classes = {}
    raw_members = []
    current_owner = None

    # ProGuard files can refer to a class before its mapping line appears.
    # Collect all class names first so every member descriptor is remapped consistently.
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw or raw.lstrip().startswith("#"):
            continue
        if not raw[0].isspace():
            match = CLASS_LINE.match(raw.strip())
            if not match:
                continue
            original, obfuscated = match.groups()
            if original in classes and classes[original] != obfuscated:
                raise ValueError(f"line {number}: duplicate class mapping for {original}")
            classes[original] = obfuscated
            current_owner = original
            continue
        if current_owner is not None:
            raw_members.append((number, current_owner, raw.strip()))

    if not classes:
        raise ValueError("mapping file contains no class mappings")

    members = []
    for number, current_owner, line in raw_members:
        if " -> " not in line:
            continue
        left, obfuscated_name = line.rsplit(" -> ", 1)
        left = strip_line_numbers(left.strip())
        obfuscated_name = obfuscated_name.strip()
        if not obfuscated_name or any(ch.isspace() for ch in obfuscated_name):
            raise ValueError(f"line {number}: invalid obfuscated member name")

        method = METHOD.match(left)
        if method:
            return_type, method_name, arguments = method.groups()
            args = [] if not arguments.strip() else [part.strip() for part in arguments.split(",")]
            descriptor = "(" + "".join(java_type_descriptor(arg, classes) for arg in args)
            descriptor += ")" + java_type_descriptor(return_type, classes)
            members.append((current_owner, "m", descriptor, obfuscated_name, method_name))
        else:
            parts = left.rsplit(None, 1)
            if len(parts) != 2:
                raise ValueError(f"line {number}: unsupported member mapping: {line}")
            field_type, field_name = parts
            descriptor = java_type_descriptor(field_type, classes)
            members.append((current_owner, "f", descriptor, obfuscated_name, field_name))
    return classes, members


def convert(text):
    classes, members = parse_mapping(text)
    lines = ["tiny\t2\t0\tofficial\tnamed"]
    obfuscated_to_original = sorted(
        ((internal(obfuscated), internal(original)) for original, obfuscated in classes.items()),
        key=lambda item: (item[0], item[1]),
    )
    members_by_owner = {}
    for owner, kind, descriptor, source_name, target_name in members:
        members_by_owner.setdefault(owner, []).append((kind, descriptor, source_name, target_name))

    for obfuscated, original in obfuscated_to_original:
        lines.append(f"c\t{obfuscated}\t{original}")
        owner_original = original.replace("/", ".")
        for kind, descriptor, source_name, target_name in sorted(
            members_by_owner.get(owner_original, []),
            key=lambda item: (item[0], item[1], item[2], item[3]),
        ):
            lines.append(f"\t{kind}\t{descriptor}\t{source_name}\t{target_name}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="local official ProGuard mapping file")
    parser.add_argument("--output", required=True, type=Path, help="local Tiny v2 output path")
    args = parser.parse_args()
    source = args.input.read_text(encoding="utf-8")
    result = convert(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8", newline="\n")
    print(f"Converted local mappings: {args.input} -> {args.output}")


if __name__ == "__main__":
    main()
