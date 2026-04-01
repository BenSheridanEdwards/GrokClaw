import plistlib
import unittest
from pathlib import Path


class HealthScheduleTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]

    def _load_plist(self, name: str) -> dict:
        path = self.workspace / "launchd" / name
        self.assertTrue(path.exists(), f"missing launchd plist: {name}")
        return plistlib.loads(path.read_bytes())

    def test_doctor_runs_on_fixed_quarter_hour_offsets(self):
        payload = self._load_plist("com.grokclaw.doctor.plist")
        self.assertNotIn("StartInterval", payload)
        intervals = payload["StartCalendarInterval"]
        minutes = {entry["Minute"] for entry in intervals}
        self.assertEqual(minutes, {2, 17, 32, 47})

    def test_gateway_watchdog_has_repo_managed_schedule(self):
        payload = self._load_plist("com.grokclaw.gateway-watchdog.plist")
        intervals = payload["StartCalendarInterval"]
        minutes = {entry["Minute"] for entry in intervals}
        self.assertEqual(minutes, {1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56})


if __name__ == "__main__":
    unittest.main()
