import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class AlphaPolymarketDeterministicTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[1]
        self.script = self.repo / "tools" / "_alpha_polymarket_deterministic.py"

    def _write_stub(self, path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def test_deterministic_flow_emits_research_telegram_and_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools = workspace / "tools"
            audit_log = workspace / "data" / "audit-log" / "2026-04-09.jsonl"
            report_log = workspace / "agent-report.log"
            decide_log = workspace / "decide.log"

            self._write_stub(tools / "polymarket-context.sh", "#!/bin/sh\nset -eu\necho 'context ok'\n")
            self._write_stub(
                tools / "alpha-memory-query.sh",
                "#!/bin/sh\nset -eu\necho \"$1 lookup ok\"\n",
            )
            self._write_stub(
                tools / "polymarket-trade.sh",
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' '{"market_id":"m1","condition_id":"c1","question":"Will X resolve?","odds_yes":0.98,"odds_no":0.02,"volume":12000,"selection_source":"bonding_copy","copy_strategy":{"status":"ok","consensus_probability_yes":0.985,"confidence":0.8,"traders_with_matching_positions":2}}'
                    """
                ),
            )
            self._write_stub(
                tools / "polymarket-decide.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{decide_log}"
                    printf '%s\\n' '{{"action":"trade","reasoning":"deterministic trade","edge":0.02,"stake_amount":8.47}}'
                    """
                ),
            )
            self._write_stub(tools / "polymarket-resolve-turn.sh", "#!/bin/sh\nset -eu\necho '{}'\n")
            self._write_stub(tools / "alpha-memory-ingest.sh", "#!/bin/sh\nset -eu\nexit 0\n")
            self._write_stub(
                tools / "telegram-post.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    mkdir -p "{audit_log.parent}"
                    printf '{{"ts":"2026-04-09T08:50:00Z","kind":"telegram_post","topic":"%s","message":"%s"}}\\n' "$1" "$2" >> "{audit_log}"
                    """
                ),
            )
            self._write_stub(
                tools / "agent-report.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{report_log}"
                    """
                ),
            )

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["ALPHA_NOW"] = "2026-04-09T08:50:00Z"
            env["CRON_RUN_ID"] = "alpha-det-test"
            result = subprocess.run(
                ["python3", str(self.script), str(workspace)],
                cwd=str(self.repo),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout.strip())
            self.assertEqual(output["decisionAction"], "trade")
            self.assertEqual(output["selectionSource"], "bonding_copy")

            research = workspace / "data" / "alpha" / "research" / "2026-04-09-08.md"
            self.assertTrue(research.exists())
            content = research.read_text(encoding="utf-8")
            self.assertIn("## Market Analysis", content)
            self.assertIn("bonding_copy", content)

            self.assertTrue(audit_log.exists())
            self.assertIn("Alpha · Hourly · TRADE", audit_log.read_text(encoding="utf-8"))
            self.assertTrue(report_log.exists())
            self.assertIn("alpha alpha-polymarket", report_log.read_text(encoding="utf-8"))
            self.assertIn("YES", decide_log.read_text(encoding="utf-8"))

    def test_deterministic_flow_skips_when_copy_signal_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools = workspace / "tools"
            decide_log = workspace / "decide.log"

            self._write_stub(tools / "polymarket-context.sh", "#!/bin/sh\nset -eu\necho 'context ok'\n")
            self._write_stub(tools / "alpha-memory-query.sh", "#!/bin/sh\nset -eu\necho 'memory ok'\n")
            self._write_stub(
                tools / "polymarket-trade.sh",
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' '{"market_id":"m2","condition_id":"c2","question":"Will Y happen?","odds_yes":0.55,"odds_no":0.45,"volume":9000,"selection_source":"volume_fallback","copy_strategy":{"status":"unavailable"}}'
                    """
                ),
            )
            self._write_stub(
                tools / "polymarket-decide.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{decide_log}"
                    printf '%s\\n' '{{"action":"skip","reasoning":"no edge","edge":0.0,"stake_amount":0.0}}'
                    """
                ),
            )
            self._write_stub(tools / "polymarket-resolve-turn.sh", "#!/bin/sh\nset -eu\necho '{}'\n")
            self._write_stub(tools / "alpha-memory-ingest.sh", "#!/bin/sh\nset -eu\nexit 0\n")
            self._write_stub(tools / "telegram-post.sh", "#!/bin/sh\nset -eu\nexit 0\n")
            self._write_stub(tools / "agent-report.sh", "#!/bin/sh\nset -eu\nexit 0\n")

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["ALPHA_NOW"] = "2026-04-09T09:10:00Z"
            result = subprocess.run(
                ["python3", str(self.script), str(workspace)],
                cwd=str(self.repo),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("SKIP", decide_log.read_text(encoding="utf-8"))

    def test_deterministic_flow_clamps_boundary_probability_for_decide(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools = workspace / "tools"
            decide_log = workspace / "decide.log"

            self._write_stub(tools / "polymarket-context.sh", "#!/bin/sh\nset -eu\necho 'context ok'\n")
            self._write_stub(tools / "alpha-memory-query.sh", "#!/bin/sh\nset -eu\necho 'memory ok'\n")
            self._write_stub(
                tools / "polymarket-trade.sh",
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' '{"market_id":"m3","condition_id":"c3","question":"Will Z happen?","odds_yes":1.0,"odds_no":0.0,"volume":15000,"selection_source":"bonding_copy","copy_strategy":{"status":"ok","consensus_probability_yes":1.0,"confidence":0.8,"traders_with_matching_positions":2}}'
                    """
                ),
            )
            self._write_stub(
                tools / "polymarket-decide.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    if [ "${{2:-}}" = "1.0000" ] || [ "${{2:-}}" = "0.0000" ]; then
                      echo "boundary probability rejected" >&2
                      exit 1
                    fi
                    printf '%s\\n' "$*" >> "{decide_log}"
                    printf '%s\\n' '{{"action":"trade","reasoning":"bounded prob","edge":0.01,"stake_amount":5.0}}'
                    """
                ),
            )
            self._write_stub(tools / "polymarket-resolve-turn.sh", "#!/bin/sh\nset -eu\necho '{}'\n")
            self._write_stub(tools / "alpha-memory-ingest.sh", "#!/bin/sh\nset -eu\nexit 0\n")
            self._write_stub(tools / "telegram-post.sh", "#!/bin/sh\nset -eu\nexit 0\n")
            self._write_stub(tools / "agent-report.sh", "#!/bin/sh\nset -eu\nexit 0\n")

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["ALPHA_NOW"] = "2026-04-09T10:40:00Z"
            result = subprocess.run(
                ["python3", str(self.script), str(workspace)],
                cwd=str(self.repo),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            args = decide_log.read_text(encoding="utf-8")
            self.assertNotIn(" 1.0000 ", f" {args} ")
            self.assertNotIn(" 0.0000 ", f" {args} ")

    def test_deterministic_flow_skips_non_bonding_copy_sources(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            tools = workspace / "tools"
            decide_log = workspace / "decide.log"

            self._write_stub(tools / "polymarket-context.sh", "#!/bin/sh\nset -eu\necho 'context ok'\n")
            self._write_stub(tools / "alpha-memory-query.sh", "#!/bin/sh\nset -eu\necho 'memory ok'\n")
            self._write_stub(
                tools / "polymarket-trade.sh",
                textwrap.dedent(
                    """\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' '{"market_id":"m4","condition_id":"c4","question":"Will A happen?","odds_yes":0.7,"odds_no":0.3,"volume":22000,"selection_source":"whale_top_trader_copy","copy_strategy":{"status":"ok","consensus_probability_yes":0.78,"confidence":0.86,"traders_with_matching_positions":4}}'
                    """
                ),
            )
            self._write_stub(
                tools / "polymarket-decide.sh",
                textwrap.dedent(
                    f"""\
                    #!/bin/sh
                    set -eu
                    printf '%s\\n' "$*" >> "{decide_log}"
                    printf '%s\\n' '{{"action":"skip","reasoning":"non-bonding blocked","edge":0.0,"stake_amount":0.0}}'
                    """
                ),
            )
            self._write_stub(tools / "polymarket-resolve-turn.sh", "#!/bin/sh\nset -eu\necho '{}'\n")
            self._write_stub(tools / "alpha-memory-ingest.sh", "#!/bin/sh\nset -eu\nexit 0\n")
            self._write_stub(tools / "telegram-post.sh", "#!/bin/sh\nset -eu\nexit 0\n")
            self._write_stub(tools / "agent-report.sh", "#!/bin/sh\nset -eu\nexit 0\n")

            env = os.environ.copy()
            env["WORKSPACE_ROOT"] = str(workspace)
            env["ALPHA_NOW"] = "2026-04-09T11:40:00Z"
            result = subprocess.run(
                ["python3", str(self.script), str(workspace)],
                cwd=str(self.repo),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("SKIP", decide_log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
