"""Fresh-interpreter measurements with logs and explicit timeout classification."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

from .common import ROOT, dump


def run_subject(subject, output, nodes=None, trace=False, timeout=40, profile=False):
    subject, output = Path(subject).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    command = [sys.executable]
    if profile:
        command += ['-m', 'cProfile', '-o', str(output / 'baseline.pstats')]
    command += ['-m', 'selci.runner', '--subject', str(subject), '--out', str(output)]
    if nodes is not None:
        dump(output / 'selected_nodes.json', nodes)
        command += ['--nodes', str(output / 'selected_nodes.json')]
    if trace:
        command += ['--trace']
    env = os.environ.copy()
    env.update(PYTHONPATH=str(ROOT), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
               PYTHONDONTWRITEBYTECODE='1', PYTHONHASHSEED='0')
    start = time.perf_counter_ns()
    with (output / 'stdout.log').open('w') as log:
        child = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        expired = threading.Event()
        def expire():
            if child.poll() is None:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                    expired.set()
                except ProcessLookupError:
                    pass
        # A blocking wait returns as soon as the child exits. wait(timeout=...)
        # polls on POSIX and would quantize these short trials by tens of ms.
        timer = threading.Timer(timeout, expire)
        timer.daemon = True
        timer.start()
        code = child.wait()
        timer.cancel()
        timer.join()
        timed_out = expired.is_set()
    wall_ns = time.perf_counter_ns() - start
    record = {'command': command, 'wall_ns': wall_ns, 'exit_code': code,
              'timed_out': timed_out, 'timeout_s': timeout,
              'timing_scope': 'Fresh interpreter, imports, collection, test phases and JSON output; no coverage or cProfile unless explicitly flagged.',
              'trace': trace, 'cprofile': profile}
    dump(output / 'process.json', record)
    return record
