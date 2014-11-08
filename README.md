Heat Convergence Prototype
==========================

This is a simple prototype to help prove the concepts behind the proposed new
"Convergence" architecture for OpenStack Heat.

It uses a trivial in-memory datastore and an event loop within a single process
to simulate multiple processes with asynchronous message passing. Note that it
**cannot** simulate race conditions or other concurrency errors, since only one
event is ever processed at a time.

Run the code by typing `python -m converge`.
