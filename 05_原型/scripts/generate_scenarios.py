"""Compatibility entry for the current acceptance runner.

Uses the same --run-id/--output-dir/--private-scenarios arguments as
run_acceptance.py. Public synthetic scenarios are the default; private scenario
selection is explicit and external. No embedded competition data or answers.
"""
from run_acceptance import main

if __name__ == '__main__':
    main()
