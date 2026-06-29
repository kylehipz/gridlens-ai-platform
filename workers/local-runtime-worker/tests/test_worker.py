import sys
from pathlib import Path
from unittest import TestCase

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from gridlens_local_runtime_worker.main import heartbeat_message


class WorkerTests(TestCase):
    def test_heartbeat_message_identifies_worker(self) -> None:
        self.assertEqual(heartbeat_message(), "gridlens local runtime worker ready")
