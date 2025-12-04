"""
Custom pytest plugin for enhanced test output
"""
import pytest
from _pytest.terminal import TerminalReporter


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "cosmetic: mark test as cosmetic enhancement"
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_terminal_summary(terminalreporter: TerminalReporter, exitstatus, config):
    """Enhanced terminal summary"""
    yield

    # Get stats
    stats = terminalreporter.stats
    passed = len(stats.get('passed', []))
    failed = len(stats.get('failed', []))
    skipped = len(stats.get('skipped', []))
    errors = len(stats.get('error', []))

    total = passed + failed + skipped + errors
    executed = passed + failed + errors

    # Custom summary table
    terminalreporter.write_sep("=", "ENHANCED TEST SUMMARY", bold=True, cyan=True)
    terminalreporter.write_line("")

    # Metrics table
    terminalreporter.write_line("┌─────────────────────────┬─────────┬──────────┬────────┐")
    terminalreporter.write_line("│ Metric                  │  Count  │  Total   │   %    │")
    terminalreporter.write_line("├─────────────────────────┼─────────┼──────────┼────────┤")

    # PASSED / ALL TESTS
    pass_pct = (passed / total * 100) if total > 0 else 0
    terminalreporter.write_line(
        f"│ PASSED / ALL TESTS      │ {passed:>7} │ {total:>8} │ {pass_pct:>5.1f}% │"
    )

    # PASSED / EXECUTED
    pass_exec_pct = (passed / executed * 100) if executed > 0 else 0
    terminalreporter.write_line(
        f"│ PASSED / EXECUTED       │ {passed:>7} │ {executed:>8} │ {pass_exec_pct:>5.1f}% │"
    )

    # (PASSED + SKIPPED) / ALL
    pass_skip_pct = ((passed + skipped) / total * 100) if total > 0 else 0
    terminalreporter.write_line(
        f"│ PASSED+SKIP / ALL       │ {passed + skipped:>7} │ {total:>8} │ {pass_skip_pct:>5.1f}% │"
    )

    terminalreporter.write_line("└─────────────────────────┴─────────┴──────────┴────────┘")
    terminalreporter.write_line("")

    # Individual stats
    if failed > 0:
        terminalreporter.write_line(f"  FAILED:   {failed}", red=True)
    if skipped > 0:
        terminalreporter.write_line(f"  SKIPPED:  {skipped}", yellow=True)
    if errors > 0:
        terminalreporter.write_line(f"  ERRORS:   {errors}", red=True)

    terminalreporter.write_line("")

    # Add coverage legend
    terminalreporter.write_sep("-", "COVERAGE LEGEND", cyan=True)
    terminalreporter.write_line("  Stmts   = Statements (executable lines of code)")
    terminalreporter.write_line("  Miss    = Missing (lines not executed by tests)")
    terminalreporter.write_line("  Cover   = Coverage percentage")
    terminalreporter.write_line("")
