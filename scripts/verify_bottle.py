#!/usr/bin/env python3
"""Verify that XSHELF bottling preserves its signed release binary."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import tarfile
import tempfile
import urllib.request


RELEASE = "https://github.com/fugamante/XSHELF/releases/download/v2026.08.29"
SOURCE_REVISION = "b8ea981b5ea0e6a64bfd92b87611f954d3c6288e"
PKG_VERSION = "2026.08.29_1"
TARGETS = {
    "arm64": {
        "archive": "xshelf-2026.08.29-aarch64-apple-darwin.tar.gz",
        "sha256": "8805b084205cbb5641cdd95099d5bffa615ca9d68f80a7823a4277b3279d0a23",
        "notary_sha256": "808d2d652d3395365139dd145993fe53cf9dc41583bf942e9e4fc970d097540c",
        "cdhash": "fccc78e1e8065f93334df21b156d983197a49bf5",
        "target": "aarch64-apple-darwin",
    },
    "x86_64": {
        "archive": "xshelf-2026.08.29-x86_64-apple-darwin.tar.gz",
        "sha256": "86a4539e93d721a25ee959d802010f2c3897b84538237a63f75ae358b21a9e9c",
        "notary_sha256": "165a39f642bd3740ccf8e17e2ebb773ce5471d023bcf2be21e6b21639530c0b8",
        "cdhash": "b55a1eaf28e0f8e5887d6876e1e83335caa2cb12",
        "target": "x86_64-apple-darwin",
    },
}


def digest(path: pathlib.Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def download(url: str, path: pathlib.Path) -> None:
    with urllib.request.urlopen(url, timeout=60) as response, path.open("wb") as output:
        while block := response.read(1024 * 1024):
            output.write(block)


def extract_binary(archive: pathlib.Path, destination: pathlib.Path) -> pathlib.Path:
    with tarfile.open(archive, "r:gz") as bundle:
        members = [
            member
            for member in bundle.getmembers()
            if member.isfile() and member.name.endswith("/bin/xshelf")
        ]
        if len(members) != 1:
            raise RuntimeError(f"expected one xshelf binary in {archive}, found {len(members)}")
        source = bundle.extractfile(members[0])
        if source is None:
            raise RuntimeError(f"could not read {members[0].name}")
        destination.write_bytes(source.read())
        destination.chmod(0o755)
    return destination


def signature(path: pathlib.Path) -> dict[str, str | bool]:
    subprocess.run(
        ["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(path)],
        check=True,
    )
    result = subprocess.run(
        ["codesign", "-d", "--verbose=4", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    metadata = result.stderr
    cdhash = re.search(r"^CDHash=([0-9a-f]+)$", metadata, re.MULTILINE)
    if cdhash is None:
        raise RuntimeError(f"CDHash missing for {path}")
    return {
        "cdhash": cdhash.group(1),
        "hardened_runtime": bool(re.search(r"^CodeDirectory .*flags=.*runtime", metadata, re.MULTILINE)),
        "secure_timestamp": bool(re.search(r"^Timestamp=.+$", metadata, re.MULTILINE)),
    }


def bottle_files() -> tuple[pathlib.Path, pathlib.Path]:
    json_files = sorted(pathlib.Path.cwd().glob("xshelf--*.bottle.json"))
    archives = sorted(pathlib.Path.cwd().glob("xshelf--*.bottle*.tar.gz"))
    if len(json_files) != 1 or len(archives) != 1:
        raise RuntimeError(
            f"expected one bottle JSON and archive, found {len(json_files)} JSON and {len(archives)} archives"
        )
    return json_files[0], archives[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-arch", choices=sorted(TARGETS), required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--installed-binary", type=pathlib.Path)
    args = parser.parse_args()

    if not re.fullmatch(r"[0-9a-f]{40}", args.expected_head):
        raise RuntimeError("expected head must be a full lowercase SHA-1")
    target = TARGETS[args.expected_arch]
    bottle_json_path, bottle_archive = bottle_files()
    bottle_json = json.loads(bottle_json_path.read_text())
    if len(bottle_json) != 1:
        raise RuntimeError("bottle JSON must contain exactly one formula")
    record = next(iter(bottle_json.values()))
    formula = record["formula"]
    bottle = record["bottle"]
    tags = bottle["tags"]
    if formula["pkg_version"] != PKG_VERSION:
        raise RuntimeError(f"unexpected bottle package version: {formula['pkg_version']}")
    if formula["tap_git_revision"] != args.expected_head:
        raise RuntimeError("bottle formula revision does not match reviewed head")
    if bottle["cellar"] != "any_skip_relocation":
        raise RuntimeError(f"bottle is not relocatable: {bottle['cellar']}")
    if len(tags) != 1:
        raise RuntimeError(f"expected one platform tag, found {sorted(tags)}")
    tag, tag_record = next(iter(tags.items()))
    if tag_record["tab"]["arch"] != args.expected_arch:
        raise RuntimeError(f"bottle architecture mismatch: {tag_record['tab']['arch']}")
    if tag_record["tab"]["binary_relocation_files"]:
        raise RuntimeError("Homebrew reports Mach-O relocation")
    if tag_record["binary_relocation_diagnostics"]:
        raise RuntimeError("Homebrew reports binary relocation diagnostics")
    if digest(bottle_archive) != tag_record["sha256"]:
        raise RuntimeError("bottle archive checksum mismatch")

    with tempfile.TemporaryDirectory(prefix="xshelf-bottle-proof.") as raw_tmp:
        temp = pathlib.Path(raw_tmp)
        source_archive = temp / str(target["archive"])
        notary_path = temp / "notary.json"
        source_binary = temp / "source-xshelf"
        bottle_binary = temp / "bottle-xshelf"
        download(f"{RELEASE}/{target['archive']}", source_archive)
        download(f"{RELEASE}/{target['archive']}.notary.json", notary_path)
        if digest(source_archive) != target["sha256"]:
            raise RuntimeError("public source archive checksum mismatch")
        if digest(notary_path) != target["notary_sha256"]:
            raise RuntimeError("public notarization evidence checksum mismatch")
        notary = json.loads(notary_path.read_text())
        required_notary = {
            "artifact_sha256": target["sha256"],
            "code_directory_hash": target["cdhash"],
            "hardened_runtime": True,
            "notarization_status": "Accepted",
            "secure_timestamp": True,
            "source_revision": SOURCE_REVISION,
            "target": target["target"],
        }
        for key, expected in required_notary.items():
            if notary.get(key) != expected:
                raise RuntimeError(f"notarization evidence mismatch for {key}")

        extract_binary(source_archive, source_binary)
        extract_binary(bottle_archive, bottle_binary)
        source_signature = signature(source_binary)
        bottle_signature = signature(bottle_binary)
        if digest(source_binary) != digest(bottle_binary):
            raise RuntimeError("bottling changed the Mach-O bytes")
        if source_signature != bottle_signature:
            raise RuntimeError("bottling changed code-signature evidence")
        if source_signature["cdhash"] != notary["code_directory_hash"]:
            raise RuntimeError("public notarization CDHash does not match the source binary")
        if not source_signature["hardened_runtime"] or not source_signature["secure_timestamp"]:
            raise RuntimeError("runtime or secure timestamp is missing")

        if args.installed_binary is not None:
            installed_signature = signature(args.installed_binary)
            if digest(args.installed_binary) != digest(source_binary):
                raise RuntimeError("installed Mach-O bytes differ from the signed release")
            if installed_signature != source_signature:
                raise RuntimeError("installed code-signature evidence differs from the signed release")

        proof = {
            "contract_version": "xshelf-bottle-proof.v1",
            "reviewed_head": args.expected_head,
            "architecture": args.expected_arch,
            "platform_tag": tag,
            "cellar": bottle["cellar"],
            "bottle_sha256": digest(bottle_archive),
            "source_archive": target["archive"],
            "source_archive_sha256": target["sha256"],
            "source_binary_sha256": digest(source_binary),
            "code_directory_hash": source_signature["cdhash"],
            "hardened_runtime": source_signature["hardened_runtime"],
            "secure_timestamp": source_signature["secure_timestamp"],
            "notarization_status": notary["notarization_status"],
            "notarization_evidence_sha256": digest(notary_path),
        }
        pathlib.Path(f"bottle-proof.{tag}.json").write_text(
            json.dumps(proof, indent=2, sort_keys=True) + os.linesep
        )
        print(json.dumps(proof, sort_keys=True))


if __name__ == "__main__":
    main()
