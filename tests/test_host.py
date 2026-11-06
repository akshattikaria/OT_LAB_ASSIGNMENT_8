import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from oslab.experiment import parse_result,expected_operations,NUMERIC
from oslab.runtime import ROOT,qemu_arguments,source_hash,parse_timebase


def line(**changes):
    fields={'kind':'pages',**{key:0 for key in NUMERIC}};fields.update(ops=480,dt=123456,alloc=480,frees=480,alocks=961,clocks=1);fields.update(changes)
    return 'GRESULT '+' '.join(f'{key}={value}' for key,value in fields.items())+'\n'


class HostTests(unittest.TestCase):
    def test_parse_actual_counter_types(self):
        result=parse_result('xv6\n'+line()+'$ ');self.assertEqual(result['ops'],480);self.assertEqual(result['aspins'],0);self.assertIsInstance(result['dt'],int)
    def test_cache_identity(self):
        self.assertEqual(parse_result(line(kind='hotseq',lookups=12,hits=10,misses=2,probes=20))['lookups'],12)
        with self.assertRaises(ValueError):parse_result(line(lookups=12,hits=11,misses=2))
    def test_missing_and_duplicate_records(self):
        for value in ('no result',line()+line(),line().replace('GRESULT','partial')):
            with self.assertRaises(ValueError):parse_result(value)
    def test_duplicate_field_rejected(self):
        with self.assertRaises(ValueError):parse_result(line().rstrip()+' ops=480\n')
    def test_failed_guest_rejected(self):
        for prefix in ('GBENCH FAIL data\n','panic: kernel\n'):
            with self.assertRaises(ValueError):parse_result(prefix+line())
    def test_negative_and_invalid_clocks(self):
        for update in ({'dt':0},{'dt':-1},{'ops':0},{'aspins':-1},{'percpu':2},{'hash':3}):
            with self.assertRaises(ValueError):parse_result(line(**update))
    def test_unknown_schema_rejected(self):
        for value in (line(kind='invalid'),line().replace(' cspins=0',''),line().rstrip()+' extra=1\n'):
            with self.assertRaises(ValueError):parse_result(value)
    def test_operation_units(self):
        self.assertEqual(expected_operations('pages',10),480);self.assertEqual(expected_operations('fork',10),30);self.assertEqual(expected_operations('pipes',10),30)
        for kind in ('hotseq','hotrand','scan'):self.assertEqual(expected_operations(kind,10),10)
    def test_invalid_budgets_rejected(self):
        for kind,count in (('invalid',1),('pages',0),('scan',-1)):
            with self.assertRaises(ValueError):expected_operations(kind,count)
    def test_qemu_is_headless_isolated_guest(self):
        argv=qemu_arguments(ROOT,3);self.assertEqual(argv[argv.index('-smp')+1],'3');self.assertEqual(argv[argv.index('-m')+1],'128M');self.assertEqual(argv[argv.index('-nic')+1],'none');self.assertNotIn('-enable-kvm',argv)
    def test_guest_cpu_bounds(self):
        for cpus in (0,9,-1):
            with self.assertRaises(ValueError):qemu_arguments(ROOT,cpus)
    def test_source_digest_tracks_content(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'a';p.write_text('one');a=source_hash(directory);p.write_text('two');self.assertNotEqual(a,source_hash(directory))
    def test_pinned_upstream_blobs(self):
        metadata=json.loads((ROOT/'UPSTREAM.json').read_text());self.assertEqual(len(metadata['files']),82)
        for file in metadata['files']:
            data=(ROOT/'vendor'/'xv6'/file['path']).read_bytes();sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();self.assertEqual(sha,file['sha'])
    def test_saved_qemu_timebase(self):
        self.assertEqual(parse_timebase((ROOT/'validation/device_tree/virt.dtb').read_bytes()),10000000)
        with self.assertRaises(ValueError):parse_timebase(b'not a device tree')


if __name__=='__main__':unittest.main()
