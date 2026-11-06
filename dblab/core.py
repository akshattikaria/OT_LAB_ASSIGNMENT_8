import hashlib
import json
from pathlib import Path
import random
import sqlite3
from contextlib import closing

ROOT=Path(__file__).resolve().parents[1]
CITIES=tuple(f'City{i:02}' for i in range(10))
WEIGHTS={'customer':40,'station':15,'confirmed':15,'status':10,'daily':10,'city':10}
SCHEMA='''
CREATE TABLE customers(id INTEGER PRIMARY KEY, city TEXT NOT NULL);
CREATE TABLE stations(id INTEGER PRIMARY KEY, city TEXT NOT NULL);
CREATE TABLE bookings(
 id INTEGER PRIMARY KEY,
 customer_id INTEGER NOT NULL REFERENCES customers(id),
 station_id INTEGER NOT NULL REFERENCES stations(id),
 slot INTEGER NOT NULL CHECK(slot >= 0 AND slot < 8760),
 status TEXT NOT NULL CHECK(status IN ('confirmed','cancelled','pending','expired')),
 total_cents INTEGER CHECK(total_cents >= 0),
 energy_wh INTEGER CHECK(energy_wh >= 0)
);
'''
INDEXES={
 'customer_time':'CREATE INDEX customer_time ON bookings(customer_id,slot,id)',
 'station_time':'CREATE INDEX station_time ON bookings(station_id,slot)',
 'status_time':'CREATE INDEX status_time ON bookings(status,slot)',
 'station_cover':'CREATE INDEX station_cover ON bookings(station_id,slot,status,total_cents,energy_wh)',
 'time_cover':'CREATE INDEX time_cover ON bookings(slot,status,total_cents,energy_wh)',
 'confirmed_station':"CREATE INDEX confirmed_station ON bookings(station_id,slot,total_cents) WHERE status='confirmed'",
}
QUERIES={
 'customer':'''SELECT id,slot,total_cents,status FROM bookings WHERE customer_id=?
 ORDER BY slot DESC,id DESC LIMIT 20''',
 'station':'''SELECT COUNT(*),SUM(total_cents),SUM(energy_wh) FROM bookings
 WHERE station_id=? AND slot>=? AND slot<?''',
 'confirmed':'''SELECT COUNT(*),SUM(total_cents) FROM bookings
 WHERE station_id=? AND status='confirmed' AND slot>=? AND slot<?''',
 'status':'''SELECT id,slot,station_id,total_cents FROM bookings
 WHERE status=? AND slot>=? AND slot<? ORDER BY slot,id LIMIT 80''',
 'daily':'''SELECT slot/24 AS day,COUNT(*),SUM(total_cents) FROM bookings
 WHERE slot>=? AND slot<? GROUP BY day ORDER BY day''',
 'city':'''SELECT s.city,COUNT(*),SUM(b.total_cents) FROM stations AS s
 JOIN bookings AS b ON b.station_id=s.id
 WHERE s.city=? AND b.slot>=? AND b.slot<? AND b.status='confirmed'
 GROUP BY s.city ORDER BY s.city''',
}


def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def fingerprint(rows):
    return hashlib.sha256(json.dumps(rows,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()


def sha_file(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def connect(path,readonly=False):
    path=Path(path).resolve()
    connection=sqlite3.connect(path.as_uri()+'?mode=ro' if readonly else str(path),uri=readonly,isolation_level=None)
    connection.execute('PRAGMA foreign_keys=ON');connection.execute('PRAGMA automatic_index=ON')
    connection.execute('PRAGMA cache_size=-8192');connection.execute('PRAGMA temp_store=MEMORY');connection.execute('PRAGMA mmap_size=0')
    connection.execute('PRAGMA threads=1')
    if not readonly:
        connection.execute('PRAGMA journal_mode=DELETE');connection.execute('PRAGMA synchronous=FULL')
    connection.execute('SELECT SUM(pgsize) FROM dbstat').fetchone()
    return connection


def generate_rows(count=200000,seed=241070005,start_id=1):
    if not isinstance(count,int) or count<1:raise ValueError('Positive row count required')
    r=random.Random(seed);result=[]
    for identifier in range(start_id,start_id+count):
        customer=r.randint(1,1000 if r.random()<.65 else 20000)
        station=r.randint(1,60 if r.random()<.60 else 600)
        slot=r.randrange(5880,8760) if r.random()<.6 else r.randrange(8760)
        status=r.choices(('confirmed','cancelled','pending','expired'),(.55,.20,.15,.10))[0]
        energy=None if r.random()<.01 else r.randint(2000,80000)
        cents=None if r.random()<.02 else (energy or 2000)*r.randint(12,28)//100
        result.append((identifier,customer,station,slot,status,cents,energy))
    return result


def cases():
    result=[]
    for split,choices in [('train',[(17,17,4000,4168,'pending','City01'),(877,53,8000,8168,'confirmed','City03')]),
                          ('heldout',[(37,3,6000,6024,'cancelled','City00'),(5791,200,8200,8536,'pending','City06'),(19997,580,1000,1720,'expired','City09')])]:
        for i,(customer,station,lo,hi,status,city) in enumerate(choices):
            params={'customer':(customer,),'station':(station,lo,hi),'confirmed':(station,lo,hi),'status':(status,lo,hi),'daily':(lo,hi),'city':(city,lo,hi)}
            for kind in QUERIES:result.append({'id':f'{split}_{kind}_{i}','split':split,'kind':kind,'params':list(params[kind])})
    return result


def sqlsum(values):
    values=[v for v in values if v is not None];return sum(values) if values else None


def reference(rows,case):
    kind=case['kind'];p=case['params']
    if kind=='customer':return [(r[0],r[3],r[5],r[4]) for r in sorted((r for r in rows if r[1]==p[0]),key=lambda r:(r[3],r[0]),reverse=True)[:20]]
    if kind in ('station','confirmed'):
        selected=[r for r in rows if r[2]==p[0] and p[1]<=r[3]<p[2] and (kind!='confirmed' or r[4]=='confirmed')]
        return [(len(selected),sqlsum([r[5] for r in selected]),sqlsum([r[6] for r in selected]))] if kind=='station' else [(len(selected),sqlsum([r[5] for r in selected]))]
    if kind=='status':return [(r[0],r[3],r[2],r[5]) for r in sorted((r for r in rows if r[4]==p[0] and p[1]<=r[3]<p[2]),key=lambda r:(r[3],r[0]))[:80]]
    if kind=='daily':
        grouped={}
        for r in rows:
            if p[0]<=r[3]<p[1]:grouped.setdefault(r[3]//24,[]).append(r[5])
        return [(day,len(values),sqlsum(values)) for day,values in sorted(grouped.items())]
    if kind=='city':
        selected=[r for r in rows if CITIES[(r[2]-1)%10]==p[0] and p[1]<=r[3]<p[2] and r[4]=='confirmed']
        return [(p[0],len(selected),sqlsum([r[5] for r in selected]))] if selected else []
    raise ValueError('Unknown query')


def populate(path,count=200000,seed=241070005):
    path=Path(path)
    if path.exists():raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True);rows=generate_rows(count,seed)
    with closing(connect(path)) as c:
        c.execute('PRAGMA page_size=4096');c.executescript(SCHEMA);c.execute('BEGIN')
        c.executemany('INSERT INTO customers VALUES(?,?)',[(i,CITIES[(i-1)%10]) for i in range(1,20001)])
        c.executemany('INSERT INTO stations VALUES(?,?)',[(i,CITIES[(i-1)%10]) for i in range(1,601)])
        c.executemany('INSERT INTO bookings VALUES(?,?,?,?,?,?,?)',rows);c.execute('COMMIT');c.execute('ANALYZE')
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok';assert not c.execute('PRAGMA foreign_key_check').fetchall()
        assert fingerprint(c.execute('SELECT * FROM bookings ORDER BY id').fetchall())==fingerprint(rows)
        facts={'rows':count,'customers':20000,'stations':600,'seed':seed,'logical_rows_sha256':fingerprint(rows),
               'status_counts':dict(c.execute('SELECT status,COUNT(*) FROM bookings GROUP BY status').fetchall()),
               'nulls':c.execute('SELECT SUM(total_cents IS NULL),SUM(energy_wh IS NULL) FROM bookings').fetchone(),
               'page_size':c.execute('PRAGMA page_size').fetchone()[0]}
    facts.update(file_bytes=path.stat().st_size,file_sha256=sha_file(path));return rows,facts
