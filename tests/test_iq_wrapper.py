import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class IqWrapperTests(unittest.TestCase):
    def test_resolves_installed_neighbor_and_configured_project_from_other_cwd(self):
        source = Path(__file__).resolve().parents[1] / "scripts/hermes_cron_codex_radar_iq_table.py"
        for configured in (False, True):
            with self.subTest(configured=configured), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                wrapper = root / "scripts/codex_radar_iq_table.py"
                wrapper.parent.mkdir()
                shutil.copyfile(source, wrapper)
                project = root / ("custom project" if configured else "codex-radar-push")
                entry = project / "scripts/codex_radar_iq_table.py"
                entry.parent.mkdir(parents=True)
                entry.write_text('if __name__ == "__main__": print("正确入口")', encoding="utf-8")
                env = dict(os.environ)
                env.pop("CODEX_RADAR_PROJECT_DIR", None)
                if configured:
                    env["CODEX_RADAR_PROJECT_DIR"] = str(project)
                result = subprocess.run([sys.executable, str(wrapper)], cwd=root.parent,
                                        env=env, text=True, capture_output=True, check=True)
                self.assertEqual(result.stdout.strip(), "正确入口")
