"""Run the CTFd test suites in groups, in a set order, optionally in parallel.

Examples:
    python run_tests.py                       run everything, one test at a time
    python run_tests.py --suite quick         run the quick suite (smoke + auth)
    python run_tests.py --group challenges    run one group
    python run_tests.py --workers 3           run the tests of each group in parallel
    python run_tests.py --delay 2             slow down so a viewer can follow
    python run_tests.py --list                show what would run, in order
"""
import argparse
import importlib
import io
import os
import sys
import unittest
from concurrent.futures import ProcessPoolExecutor

import test_config


def get_args():
    parser = argparse.ArgumentParser(description="Run the CTFd Selenium tests")
    parser.add_argument("--suite", choices=list(test_config.SUITES), default="full",
                        help="named set of groups (default: full)")
    parser.add_argument("--group", nargs="+", choices=list(test_config.GROUPS),
                        help="run only these groups (overrides --suite)")
    parser.add_argument("--workers", type=int, default=1,
                        help="number of tests to run at the same time (default: 1)")
    parser.add_argument("--delay", type=float, default=0,
                        help="seconds to pause in each test so it can be watched (default: 0)")
    parser.add_argument("--list", action="store_true",
                        help="only print the groups and tests in run order")
    return parser.parse_args()


def class_test_ids(class_path):
    """Return the test ids of one class, sorted by METHOD_ORDER."""
    module_name, class_name = class_path.rsplit(".", 1)
    test_class = getattr(importlib.import_module(module_name), class_name)
    names = unittest.TestLoader().getTestCaseNames(test_class)
    order = test_config.METHOD_ORDER.get(class_name, [])

    def sort_key(name):
        for position, prefix in enumerate(order):
            if name.startswith(prefix):
                return (position, name)
        return (len(order), name)

    return [class_path + "." + name for name in sorted(names, key=sort_key)]


def group_test_ids(group_name):
    ids = []
    for class_path in test_config.GROUPS[group_name]:
        ids += class_test_ids(class_path)
    return ids


def run_one(test_id):
    """Run a single test (used by the parallel workers)."""
    suite = unittest.TestLoader().loadTestsFromName(test_id)
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=0).run(suite)
    return test_id, result.wasSuccessful(), output.getvalue()


def run_group_in_order(test_ids):
    """Run the tests one after another, in the given order."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for test_id in test_ids:
        suite.addTests(loader.loadTestsFromName(test_id))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return result.testsRun, len(result.failures) + len(result.errors)


def run_group_in_parallel(test_ids, workers):
    """Run the tests of a group at the same time, each in its own process."""
    failed = 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for test_id, passed, output in pool.map(run_one, test_ids):
            print(("PASS  " if passed else "FAIL  ") + test_id)
            if not passed:
                failed += 1
                print(output)
    return len(test_ids), failed


def main():
    args = get_args()
    os.environ["STEP_DELAY"] = str(args.delay)  # read by the test files

    wanted = args.group if args.group else test_config.SUITES[args.suite]
    # the groups always run in the order written in test_config.GROUPS
    groups = [name for name in test_config.GROUPS if name in wanted]

    if args.list:
        for name in groups:
            print("\n[" + name + "]")
            for test_id in group_test_ids(name):
                print("  " + test_id)
        return 0

    total, failed = 0, 0
    for name in groups:
        print("\n===== group: " + name + " =====")
        test_ids = group_test_ids(name)
        if args.workers > 1:
            ran, bad = run_group_in_parallel(test_ids, args.workers)
        else:
            ran, bad = run_group_in_order(test_ids)
        print("group " + name + ": " + str(ran) + " run, " + str(bad) + " failed")
        total += ran
        failed += bad

    print("\nTOTAL: " + str(total) + " run, " + str(failed) + " failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
