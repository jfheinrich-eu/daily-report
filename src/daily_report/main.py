"""Main entry point for the Daily Reporter application.
This script initializes and runs the DailyReporter class."""

from .daily_reporter import DailyReporter

if __name__ == "__main__":
    reporter = DailyReporter()
    reporter.run()
