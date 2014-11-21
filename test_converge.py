#!/usr/bin/env python

import functools
import logging
import unittest

import converge
import converge.processes

from converge.framework import datastore
from converge.framework import scenario


def with_scenarios(TestCase):
    loader = unittest.defaultTestLoader

    def create_test_func(generic_test, params):
        @functools.wraps(generic_test)
        def test_func(testcase, *args, **kwargs):
            for key, value in params.items():
                setattr(testcase, key, value)
            return generic_test(testcase, *args, **kwargs)

        return test_func

    for test_name in loader.getTestCaseNames(TestCase):
        base_test = getattr(TestCase, test_name)

        for scenario in getattr(TestCase, 'scenarios', []):
            name, parameters = scenario
            # if name != "basic_create" and name != "update_add":
                # continue
            test_func = create_test_func(base_test, parameters)
            setattr(TestCase, '%s(%s)' % (test_name, name), test_func)

        delattr(TestCase, test_name)

    TestCase.scenarios = None
    return TestCase


@with_scenarios
class ScenarioTest(unittest.TestCase):

    scenarios = [(name, {'name': name, 'path': path})
                    for name, path in scenario.list_all('scenarios')]

    def setUp(self):
        self.maxDiff = None
        super(ScenarioTest, self).setUp()
        self.procs = converge.processes.Processes()

    def tearDown(self):
        datastore.Datastore.clear_all()
        super(ScenarioTest, self).tearDown()

    def test_scenario(self):
        runner = scenario.Scenario(self.name, self.path)
        runner(self.procs.event_loop,
               **converge.scenario_globals(self.procs, self))


if __name__ == '__main__':
    # converge.setup_log(logging.root)
    unittest.main()
