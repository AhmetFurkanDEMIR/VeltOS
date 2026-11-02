"""The ISO build's own tools: the package pool trimmer and the initrd packer
(build/scripts/trim-pool.py, shrink-initrd.py), which keep the ISO under
2 GiB without leaving anything out."""

import importlib.util
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), REPO / "build/scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IsoLimitTests(unittest.TestCase):
    def test_build_fails_for_an_iso_of_2_gib_or_more(self):
        """Every ISO is a GitHub release file (under 2 GiB, product owner
        2026-10-27): build-iso.sh stops when the ISO is not smaller."""
        script = (REPO / "build/scripts/build-iso.sh").read_text(encoding="utf-8")
        self.assertIn("ISO_LIMIT=2147483648", script)
        self.assertIn('if [ "$iso_size" -ge "$ISO_LIMIT" ]; then', script)
        limit_at = script.index("ISO_LIMIT=")
        self.assertLess(limit_at, script.index("(cd \"$RESULT_DIR\" && sha256sum"))


class TrimPoolTests(unittest.TestCase):
    def setUp(self):
        self.tool = load("trim-pool")

    def test_installed_packages_from_dpkg_status(self):
        status = ("Package: libc6\nStatus: install ok installed\nArchitecture: amd64\nVersion: 2.41-12\n\n"
                  "Package: grub-pc\nStatus: deinstall ok config-files\nArchitecture: amd64\nVersion: 2.12-9\n\n"
                  "Package: os-prober\nStatus: install ok installed\nArchitecture: amd64\nVersion: 1.83\n")
        self.assertEqual(self.tool.installed(status), {("libc6", "amd64", "2.41-12"), ("os-prober", "amd64", "1.83")})

    def test_the_installers_removals(self):
        conf = (REPO / "packages/calamares-settings-veltos/calamares/modules/packages.conf").read_text()
        names = self.tool.installer_removals(conf)
        self.assertIn("live-boot", names)
        self.assertIn("calamares", names)
        self.assertNotIn("remove", names)

    def test_what_autoremove_takes_is_kept(self):
        simulation = ("NOTE: This is only a simulation!\n"
                      "Purg live-boot [1:20250225]\n"
                      "Purg kpmcore [24.12.3-1]\n"
                      "Remv libkpmcore12:amd64 [24.12.3-1]\n"
                      "Inst something\n")
        self.assertEqual(self.tool.removed_with_autoremove(simulation), {"live-boot", "kpmcore", "libkpmcore12"})

    def test_release_checksums(self):
        suite = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, suite)
        (suite / "main/binary-amd64").mkdir(parents=True)
        (suite / "main/binary-amd64/Packages").write_text("Package: grub-pc\n")
        (suite / "Release").write_text("old\n")
        text = self.tool.checksum_sections(suite)
        self.assertIn("SHA256:\n", text)
        self.assertIn(" main/binary-amd64/Packages\n", text)
        self.assertNotIn(" Release\n", text)


class ShrinkInitrdTests(unittest.TestCase):
    @staticmethod
    def newc(entries):
        """A newc cpio archive of (name, data) entries."""
        out = b""
        for ino, (name, data) in enumerate(entries + [("TRAILER!!!", b"")], 1):
            name_bytes = name.encode() + b"\0"
            header = "070701" + "".join(f"{v:08X}" for v in (ino, 0o100644, 0, 0, 1, 0, len(data), 0, 0, 0, 0,
                                                              len(name_bytes), 0))
            out += header.encode() + name_bytes
            out += b"\0" * (-len(out) % 4) + data
            out += b"\0" * (-len(out) % 4)
        return out

    @unittest.skipUnless(shutil.which("zstd") and shutil.which("xz"), "needs zstd and xz (the builder image)")
    def test_main_part_becomes_xz_and_the_rest_stays(self):
        tool = load("shrink-initrd")
        early = self.newc([("kernel/x86/microcode/GenuineIntel.bin", b"\x01" * 1000)])
        modules = self.newc([("usr/lib/modules/x.ko.xz", b"\x02" * 3000)])
        main = self.newc([("init", b"#!/bin/sh\n" * 500), ("usr/lib/firmware/a.bin", bytes(range(256)) * 400)])
        packed_main = subprocess.run(["zstd", "-q", "-c"], input=main, capture_output=True, check=True).stdout
        folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, folder)
        initrd = folder / "initrd.img"
        initrd.write_bytes(early + modules + packed_main)
        self.assertEqual(tool.shrink(str(initrd)), 0)
        data = initrd.read_bytes()
        prefix, rest = tool.split(data)
        self.assertEqual(prefix, early + modules)
        self.assertTrue(rest.startswith(tool.XZ))
        self.assertEqual(subprocess.run(["xz", "-dc"], input=rest, capture_output=True, check=True).stdout, main)
        # The kernel's xz decoder needs CRC32 checks (stream flags byte 1).
        self.assertEqual(rest[7], 0x01)
        self.assertEqual(tool.shrink(str(initrd)), 0)          # already xz: unchanged
        self.assertEqual(initrd.read_bytes(), data)


class ReleaseToolTests(unittest.TestCase):
    """The release's own tools (.github/workflows/release.yml): the version
    bump and check, the release text, the package repository for VeltOS
    Update and the website's release values."""

    def tree(self):
        """A small copy of the repository's release-relevant files."""
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        (root / "packages/veltos-base").mkdir(parents=True)
        shutil.copy(REPO / "packages/veltos-base/os-release", root / "packages/veltos-base/os-release")
        for name, version in (("veltos-base", "1.0.0"), ("veltos-ai", "1.1.0~dev4"), ("veltos-camera", "1.0.0"),
                              ("veltos-fluent-icons", "2026.07.27~veltos4")):
            path = root / f"packages/{name}/debian/changelog"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{name} ({version}) trixie; urgency=medium\n\n  * Something.\n\n"
                            " -- VeltOS Developers <x@example.invalid>  Mon, 02 Nov 2026 12:00:00 +0000\n",
                            encoding="utf-8", newline="\n")
        (root / "VERSION").write_text("1.0\n", encoding="utf-8", newline="\n")
        (root / "docs/release-notes").mkdir(parents=True)
        (root / "docs/release-notes/1.1.md").write_text("### New\n\n- A\n\n<!-- tr -->\n\n### Yeni\n\n- A\n",
                                                         encoding="utf-8", newline="\n")
        return root

    def test_bump_then_check(self):
        root = self.tree()
        check = load("release-check")
        before = check.problems("1.1", "", root=root)
        self.assertTrue(any(p.startswith("VERSION") for p in before), before)
        self.assertTrue(any("veltos-ai 1.1.0~dev4" in p for p in before), before)
        load("release-bump").main(["1.1", "--root", str(root), "--date", "Tue, 03 Nov 2026 12:00:00 +0000"])
        self.assertEqual((root / "VERSION").read_text(encoding="utf-8"), "1.1\n")
        os_release = (root / "packages/veltos-base/os-release").read_text(encoding="utf-8")
        self.assertIn('VERSION_ID="1.1"', os_release)
        self.assertIn('PRETTY_NAME="VeltOS 1.1"', os_release)

        def first(name):
            return (root / f"packages/{name}/debian/changelog").read_text(encoding="utf-8")
        self.assertTrue(first("veltos-base").startswith("veltos-base (1.1.0) trixie; urgency=medium\n\n"
                                                        "  * VeltOS 1.1.\n\n -- VeltOS Developers"))
        self.assertTrue(first("veltos-ai").startswith("veltos-ai (1.1.0) trixie"))
        self.assertIn("Tue, 03 Nov 2026 12:00:00 +0000\n\nveltos-ai (1.1.0~dev4)", first("veltos-ai"))
        self.assertTrue(first("veltos-camera").startswith("veltos-camera (1.0.0) "))       # unchanged
        self.assertTrue(first("veltos-fluent-icons").startswith("veltos-fluent-icons (2026.07.27~veltos4)"))
        self.assertEqual(check.problems("1.1", "", root=root), [])

    def test_release_text_keeps_both_languages(self):
        text = load("release-notes").compose("### New\n\n- A\n\n<!-- tr -->\n\n### Yeni\n\n- B\n",
                                             "VeltOS-1.1-amd64.iso", "a" * 64)
        english, marker, turkish = text.partition("<!-- tr -->")
        self.assertTrue(marker)
        self.assertIn("**Download:** `VeltOS-1.1-amd64.iso` · SHA-256 `" + "a" * 64 + "`", english)
        self.assertIn("**İndirme:** `VeltOS-1.1-amd64.iso`", turkish)
        self.assertNotIn("İndirme", english)
        self.assertTrue(turkish.strip().startswith("### Yeni"))

    def site_copy(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        (root / "docs").mkdir()
        for rel in ("docs/index.html", "docs/sitemap.xml", "README.md"):
            shutil.copy(REPO / rel, root / rel)
        return root

    @staticmethod
    def meta(html, name):
        return re.search(rf'<meta name="{name}" content="([^"]*)"', html).group(1)

    def test_website_update_after_a_release(self):
        site = load("update-site")
        root = self.site_copy()
        html = (REPO / "docs/index.html").read_text(encoding="utf-8")
        # With the site's own values nothing changes.
        site.main(["--root", str(root), "--version", self.meta(html, "veltos-version"),
                   "--iso-url", self.meta(html, "veltos-iso-url"), "--size", self.meta(html, "veltos-iso-size"),
                   "--sha256", self.meta(html, "veltos-iso-sha256"), "--date", self.meta(html, "veltos-release-date")])
        for rel in ("docs/index.html", "docs/sitemap.xml", "README.md"):
            self.assertEqual((root / rel).read_bytes(), (REPO / rel).read_bytes(), rel)
        url = "https://github.com/AhmetFurkanDEMIR/VeltOS/releases/download/v1.9/VeltOS-1.9-amd64.iso"
        sha = "b" * 64
        site.main(["--root", str(root), "--version", "1.9", "--iso-url", url, "--size", "2093000000",
                   "--sha256", sha, "--date", "2027-01-15"])
        new = (root / "docs/index.html").read_text(encoding="utf-8")
        readme = (root / "README.md").read_text(encoding="utf-8")
        self.assertEqual(self.meta(new, "veltos-version"), "1.9")
        self.assertEqual(self.meta(new, "veltos-release-date"), "2027-01-15")
        self.assertEqual(set(re.findall(r'data-release="version">([^<]*)<', new)), {"1.9"})
        self.assertEqual(set(re.findall(r'data-release="size">([^<]*)<', new)), {"2.1 GB"})
        self.assertEqual(set(re.findall(r'data-release="iso-name">([^<]*)<', new)), {"VeltOS-1.9-amd64.iso"})
        self.assertEqual(set(re.findall(r'data-release="date">([^<]*)<', new)), {"15 January 2027"})
        self.assertIn(f'data-release="sha-url" href="{url}.sha256"', new)
        self.assertIn(f'"downloadUrl": "{url}"', new)
        self.assertIn('"datePublished": "2027-01-15"', new)
        self.assertEqual(set(re.findall(r"\b[0-9a-f]{64}\b", new)), {sha})
        self.assertEqual(set(re.findall(r"\b[0-9a-f]{64}\b", readme)), {sha})
        self.assertIn(f"[VeltOS-1.9-amd64.iso]({url})", readme)
        self.assertIn("releases/tag/v1.9) (15 January 2027)", readme)
        self.assertIn("<lastmod>2027-01-15</lastmod>", (root / "docs/sitemap.xml").read_text(encoding="utf-8"))
        # The measurement on VeltOS 1.0 is not a release value.
        self.assertIn("installed VeltOS 1.0 (4 CPU cores", new)

    def test_website_release_values_are_marked(self):
        """The release values come from the meta tags (main.js fills both
        languages): no version, size or checksum written into a text."""
        html = (REPO / "docs/index.html").read_text(encoding="utf-8")
        script = (REPO / "docs/assets/js/main.js").read_text(encoding="utf-8")
        version = self.meta(html, "veltos-version")
        self.assertRegex(version, r"^\d+\.\d+$")
        self.assertRegex(self.meta(html, "veltos-release-date"), r"^\d{4}-\d{2}-\d{2}$")
        self.assertRegex(self.meta(html, "veltos-iso-size"), r"^\d+$")
        self.assertEqual(self.meta(html, "veltos-iso-url").rsplit("/", 1)[-1], f"VeltOS-{version}-amd64.iso")
        keys = set(re.findall(r'data-release=\\?"([^"\\]+)', html + script))
        self.assertLessEqual(keys, {"version", "size", "sha256", "iso-name", "date", "sha-url"})
        markup = re.sub(r"<!--.*?-->|<script\b.*?</script>", "", html, flags=re.S)
        for value in re.findall(r'data-(?:since|until)="([^"]*)"', markup):
            self.assertRegex(value, r"^\d+\.\d+$")
        # Turkish texts carry no hard-coded release value (a suffix after a
        # version number was the Turkish problem: "VeltOS 1.0'ı").
        turkish = script.split("var TR = {", 1)[1].split("};", 1)[0]
        for key in ("hero.eyebrow", "hero.meta", "s.title", "s.version.v", "s.iso.v", "d.title", "dl.meta",
                    "dl.hashnote", "dl.s1.d"):
            line = re.search(rf'"{re.escape(key)}": "(.*)",?$', turkish, re.M).group(1)
            self.assertNotRegex(line, r"\d+[.,]\d+ GB|VeltOS-\d|[0-9a-f]{64}|'[ıiuü]\b", key)
            self.assertIn("data-release", line, key)

    def test_release_workflow_uses_existing_tools(self):
        workflow = (REPO / ".github/workflows/release.yml").read_text(encoding="utf-8")
        run_sh = (REPO / "build/run.sh").read_text(encoding="utf-8")
        for script in set(re.findall(r"build/scripts/([\w.-]+\.(?:py|sh))", workflow)):
            self.assertTrue((REPO / "build/scripts" / script).exists(), script)
        for command in set(re.findall(r"build/run\.sh ([a-z-]+)", workflow)):
            self.assertRegex(run_sh, rf"\n\s+(?:[a-z|-]*\|)?{re.escape(command)}(?:\|[a-z|-]*)?\)", command)
        for mode in re.findall(r"build/run\.sh test (\w+)", workflow):
            self.assertIn(mode, ("uefi", "bios", "secureboot"))
        self.assertIn("secrets.VELTOS_APT_SIGNING_KEY", workflow)
        self.assertIn("--latest", workflow)
        self.assertIn("fetch-depth: 0", workflow)

    @unittest.skipUnless(shutil.which("apt-ftparchive") and shutil.which("dpkg-deb"), "needs apt-utils and dpkg")
    def test_package_repository_names_github_keeps(self):
        """GitHub renames release files with "~" or "+"; the repository's
        files and index use the names GitHub keeps."""
        work = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, work, True)
        debs = work / "debs"
        debs.mkdir()
        for name, version in (("veltos-x", "1.1.0~dev1"), ("veltos-y", "2.0+b1")):
            tree = work / name / "DEBIAN"
            tree.mkdir(parents=True)
            (tree / "control").write_text(f"Package: {name}\nVersion: {version}\nArchitecture: all\n"
                                          "Maintainer: T <t@example.invalid>\nDescription: test\n", encoding="utf-8")
            subprocess.run(["dpkg-deb", "--root-owner-group", "-b", str(work / name),
                            str(debs / f"{name}_{version}_all.deb")], check=True, capture_output=True)
        env = dict(os.environ)
        env.pop("VELTOS_APT_SIGNING_KEY", None)
        result = subprocess.run(["bash", str(REPO / "build/scripts/make-apt-repo.sh"), str(debs), str(work / "repo")],
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("not signed", result.stderr)
        files = sorted(p.name for p in (work / "repo").iterdir())
        self.assertIn("veltos-x_1.1.0-dev1_all.deb", files)
        self.assertIn("veltos-y_2.0-b1_all.deb", files)
        for name in ("Packages", "Packages.xz", "Packages.gz", "Release"):
            self.assertIn(name, files)
        index = (work / "repo/Packages").read_text(encoding="utf-8")
        self.assertIn("Filename: ./veltos-x_1.1.0-dev1_all.deb", index)
        self.assertIn("Version: 1.1.0~dev1", index)


if __name__ == "__main__":
    unittest.main()
