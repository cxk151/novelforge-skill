import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "novelforge.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


class NovelForgeTests(unittest.TestCase):
    def test_init_validate_and_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "book"
            created = run("init", project, "--title", "测试小说")
            self.assertEqual(created.returncode, 0, created.stderr)
            validated = run("validate", project)
            self.assertEqual(validated.returncode, 0, validated.stdout)
            chapter = project / "manuscript" / "第001章.md"
            chapter.write_text("# 第一章\n\n你好，世界。\n", encoding="utf-8")
            data = json.loads(run("count", chapter).stdout)
            self.assertEqual(data["cjk_characters"], 4)

    def test_audit_detects_duplicate_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "book"
            self.assertEqual(run("init", project, "--title", "测试").returncode, 0)
            (project / "manuscript" / "第001章-a.md").write_text("内容", encoding="utf-8")
            (project / "manuscript" / "chapter-001-b.md").write_text("内容", encoding="utf-8")
            audited = run("audit", project)
            self.assertEqual(audited.returncode, 1)
            self.assertIn("duplicate_chapter_number", audited.stdout)


if __name__ == "__main__":
    unittest.main()
