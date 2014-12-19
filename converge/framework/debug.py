import bdb
import contextlib
import pdb
import sys


Quit = bdb.BdbQuit


class Debugger(pdb.Pdb):
    def __init__(self):
        pdb.Pdb.__init__(self)
        self.reset()

    def begin_scenario(self):
        sys.settrace(self.trace_dispatch)

    def end_scenario(self):
        sys.settrace(None)
        self.clear_all_breaks()
        self.reset()

    def dispatch_call(self, frame, arg):
        if self.botframe is None:
            self.botframe = frame.f_back
            self._set_stopinfo(self.botframe, None, -1)
            return self.trace_dispatch
        else:
            return pdb.Pdb.dispatch_call(self, frame, arg)


@contextlib.contextmanager
def debugger(debug_enabled, procs):
    if debug_enabled:
        debugger = Debugger()
        procs.set_debugger(debugger)
        debugger.begin_scenario()
    else:
        debugger = None

    try:
        yield debugger
    except Quit:
        pass
    except Exception as exc:
        if debugger is not None:
            traceback = sys.exc_info()[2]
            debugger.interaction(None, traceback)
        else:
            raise
    finally:
        if debugger is not None:
            debugger.end_scenario()


__all__ = ['Quit', 'debugger']
