"""Recover resource measurements after completed learning stages; preserve their hashes."""
import hashlib
import json
from pathlib import Path
import sys
from .experiment import write_json,run_scheduling,run_system_controls
from .parallel import measure_inference


def resume(directory):
    root=Path(directory);protocol=json.loads((root/'protocol.json').read_text())
    if any((root/name).exists() for name in ('scheduling_runs.json','parallel_runs.json','synchronization_runs.json')):
        raise ValueError('Resource results already exist; choose a fresh benchmark output rather than overwriting them')
    names=('coverage_runs.json','federated_runs.json','centralized_runs.json','multitask_runs.json')
    hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names}
    workers=protocol['workers'];repeats=protocol['repeats']
    run_scheduling(root,workers,repeats,protocol['iterations_per_unit'])
    write_json(root/'parallel_runs.json',measure_inference(workers,repeats))
    run_system_controls(root,workers,repeats)
    write_json(root/'input_sha256.json',{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('coverage_inputs','federated_data','multitask_data') for p in sorted((root/folder).glob('*'))})
    if not all(hashlib.sha256((root/n).read_bytes()).hexdigest()==sha for n,sha in hashes.items()):raise AssertionError('Learning evidence changed')
    write_json(root/'resume_record.json',{'learning_files_unchanged':hashes,'parallel_backend':'shared-array deques with locks','tests_before_resource_measurements':29,
        'note':'Manager transport unavailable on first attempt; no timings retained. A stdin launch cannot spawn portable children and was interrupted; measurements collected using this importable guarded module.'})
    print('All Track D raw experiments complete',flush=True)


if __name__=='__main__':resume(sys.argv[1] if len(sys.argv)>1 else 'results')
