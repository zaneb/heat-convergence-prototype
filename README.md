Heat Convergence Prototype
==========================

This is a simple prototype to help prove the concepts behind the proposed new
"Convergence" architecture for OpenStack Heat.

It uses a trivial in-memory datastore and an event loop within a single process
to simulate multiple processes with asynchronous message passing. Note that it
**cannot** simulate race conditions or other concurrency errors, since only one
event is ever processed at a time.

Run the code by typing `python -m converge`.

```
Usage: /usr/bin/python -m converge [options] SCENARIOS

 An OpenStack Heat convergence algorithm simulator.

Options:
  -h, --help            show this help message and exit
  -d DIR, --scenario-directory=DIR
                        Directory to read scenarios from
  -p, --pdb             Enable debugging with pdb
```

To run a specific subset of the test scenarios, append their names to the
command line (e.g. `python -m converge basic_create`).

To automatically set debugger breakpoints at the beginning of each asynchronous
task, pass the `--pdb` option on the command line.
