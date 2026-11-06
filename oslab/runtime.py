import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import struct
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
VARIANTS={'baseline':(0,0),'percpu':(1,0),'hash':(0,1),'combined':(1,1)}


def tool_environment(toolchain=None):
    env=os.environ.copy()
    prefix=Path(toolchain) if toolchain else ROOT.parent/'tmp'/'trackg-toolchain'
    if (prefix/'usr/bin/qemu-system-riscv64').exists():
        env['PATH']=str(prefix/'usr/bin')+os.pathsep+env.get('PATH','')
        env['LD_LIBRARY_PATH']=str(prefix/'usr/lib/x86_64-linux-gnu')+os.pathsep+env.get('LD_LIBRARY_PATH','')
    for command in ('qemu-system-riscv64','riscv64-linux-gnu-gcc','riscv64-linux-gnu-objdump','make'):
        if not shutil.which(command,path=env['PATH']):raise RuntimeError(f'Missing {command}; see README toolchain setup')
    return env


def write_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def source_hash(source):
    h=hashlib.sha256()
    for file in sorted(Path(source).rglob('*')):
        if file.is_file():h.update(str(file.relative_to(source)).encode()+b'\0'+file.read_bytes())
    return h.hexdigest()


def build(variant,env,log_directory):
    if variant not in VARIANTS and variant!='pristine':raise ValueError('Unknown kernel variant')
    source=ROOT/'vendor'/'xv6' if variant=='pristine' else ROOT/'xv6';digest=source_hash(source);target=ROOT/'build'/digest[:12]/variant
    if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(source,target)
    values=VARIANTS.get(variant,(0,0));argv=['make','-j4','TOOLPREFIX=riscv64-linux-gnu-',f'KMEM_PERCPU={values[0]}',f'HASHBCACHE={values[1]}','kernel/kernel','fs.img']
    log=Path(log_directory)/f'{variant}_build.log';log.parent.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    with log.open('w') as stream:result=subprocess.run(argv,cwd=target,env=env,stdout=stream,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError(f'{variant} build failed; see {log}')
    shutil.copyfile(target/'fs.img',target/'fresh.img')
    return target,{'variant':variant,'source_sha256':digest,'command':argv,'seconds':time.monotonic()-start,'kernel_bytes':(target/'kernel/kernel').stat().st_size,'kernel_sha256':hashlib.sha256((target/'kernel/kernel').read_bytes()).hexdigest(),
        'filesystem_bytes':(target/'fresh.img').stat().st_size,'filesystem_sha256':hashlib.sha256((target/'fresh.img').read_bytes()).hexdigest()}


def qemu_arguments(directory,cpus=3,image='fs.img'):
    if not isinstance(cpus,int) or not 1<=cpus<=8:raise ValueError('Guest CPU count must be 1..8')
    return ['qemu-system-riscv64','-machine','virt','-bios','none','-kernel','kernel/kernel','-m','128M','-smp',str(cpus),'-display','none','-serial','stdio','-monitor','none','-nic','none','-global','virtio-mmio.force-legacy=false','-drive',f'file={image},if=none,format=raw,id=x0','-device','virtio-blk-device,drive=x0,bus=virtio-mmio-bus.0']


class Guest:
    def __init__(self,directory,env,log,cpus=3):
        self.directory=Path(directory);self.log=Path(log);self.log.parent.mkdir(parents=True,exist_ok=True);self.stream=self.log.open('wb');self.pending=b'';self.all=b''
        shutil.copyfile(self.directory/'fresh.img',self.directory/'run.img')
        self.argv=qemu_arguments(directory,cpus,'run.img');self.start=time.monotonic();self.process=subprocess.Popen(self.argv,cwd=directory,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        self.read_until(b'$ ',timeout=45)
    def read_until(self,marker,timeout=300):
        start=time.monotonic();data=self.pending;self.pending=b''
        while marker not in data:
            if time.monotonic()-start>timeout:raise TimeoutError(f'Guest timed out waiting for {marker!r}; see {self.log}')
            ready=select.select([self.process.stdout],[],[],.5)[0]
            if ready:
                block=os.read(self.process.stdout.fileno(),65536)
                if not block:raise RuntimeError('QEMU exited before expected output; see '+str(self.log))
                self.stream.write(block);self.stream.flush();self.all+=block;data+=block
        stop=data.index(marker)+len(marker);self.pending=data[stop:];return data[:stop].decode(errors='replace')
    def command(self,command,timeout=300):
        if '\n' in command or '\r' in command:raise ValueError('One guest command at a time')
        self.process.stdin.write(command.encode()+b'\n');self.process.stdin.flush();return self.read_until(b'$ ',timeout)
    def close(self):
        if self.process.poll() is None:self.process.terminate()
        try:self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:self.process.kill();self.process.wait()
        self.stream.close()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()


def timebase(env,directory):
    path=Path(directory).resolve()/'virt.dtb';path.parent.mkdir(parents=True,exist_ok=True)
    argv=['qemu-system-riscv64','-machine',f'virt,dumpdtb={path}','-bios','none','-m','128M','-smp','3','-display','none','-serial','none','-monitor','none','-nic','none']
    subprocess.run(argv,env=env,capture_output=True,check=True,timeout=20)
    return parse_timebase(path.read_bytes())


def parse_timebase(raw):
    if len(raw)<40 or raw[:4]!=bytes.fromhex('d00dfeed'):raise ValueError('Not a flattened device tree')
    header=struct.unpack('>10I',raw[:40]);cursor=header[2];strings=raw[header[3]:];frequency=None
    while cursor<len(raw):
        token=struct.unpack_from('>I',raw,cursor)[0];cursor+=4
        if token==1:cursor=(raw.index(b'\0',cursor)+4)&~3
        elif token==3:
            length,offset=struct.unpack_from('>II',raw,cursor);cursor+=8;name=strings[offset:strings.index(b'\0',offset)].decode();value=raw[cursor:cursor+length];cursor=(cursor+length+3)&~3
            if name=='timebase-frequency':frequency=int.from_bytes(value,'big')
        elif token==9:break
        elif token not in (2,4):raise ValueError('Malformed QEMU device tree')
    if not frequency:raise ValueError('No timebase-frequency in QEMU device tree')
    return frequency
