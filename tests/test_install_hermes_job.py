import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import install_hermes_job


class InstallHermesJobTests(unittest.TestCase):
    def test_cron_script_uses_hermes_scripts_wrapper(self):
        self.assertEqual(install_hermes_job.WRAPPER_SCRIPT, "codex_radar_refresh_watch.py")
        self.assertNotIn("/", install_hermes_job.WRAPPER_SCRIPT)

    def test_cron_schedule_checks_hourly_after_five_minutes(self):
        self.assertEqual(install_hermes_job.SCHEDULE_EXPR, "5 * * * *")

    def test_delivery_target_is_not_stored_in_source(self):
        source = Path(install_hermes_job.__file__).read_text(encoding="utf-8")
        self.assertNotIn("WEIXIN_CHAT_ID", source)
        self.assertNotIn("oc_", source)

    def test_delivery_target_is_required(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ValueError, "platform:chat_id"):
                install_hermes_job.main()


if __name__ == "__main__":
    unittest.main()
