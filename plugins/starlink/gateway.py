"""Root helper for the dedicated C3 proxy core and global/hotspot TUN routing."""
import ipaddress,json,os,pathlib,socket,subprocess,sys,shutil,signal,time,pwd
ROOT=pathlib.Path('/data/mihomo');DEV='c3mh0';TABLE='17890';PRIORITY='17890';CHAIN='C3MH_DNS';IPT='iptables-legacy';CORE_UID=61400
def run(*args,check=True):
 return subprocess.run(list(args),capture_output=True,text=True,check=check)
def hotspot():
 data=json.loads(run('ip','-j','-4','addr','show','dev','wlan0').stdout)
 addresses=[a for dev in data for a in dev['addr_info'] if a['scope']=='global']
 if not addresses:raise RuntimeError('Enable the device hotspot first')
 a=addresses[0];assert a['local']=='192.168.43.1','Hotspot mode is required'
 return a['local'],str(ipaddress.ip_network(f"{a['local']}/{a['prefixlen']}",strict=False))
def prepare():
 # Wi-Fi client mode is valid too: only add hotspot rules when its address exists.
 state=ROOT/'gateway_state.json'
 if not state.exists():state.write_text(json.dumps({'previous_forward':pathlib.Path('/proc/sys/net/ipv4/ip_forward').read_text().strip()}))
 if run('ip','link','show',DEV,check=False).returncode:
  run('ip','tuntap','add','dev',DEV,'mode','tun','user',str(CORE_UID))
 run('ip','addr','replace','198.18.0.1/30','dev',DEV);run('ip','link','set',DEV,'up')
 pathlib.Path('/proc/sys/net/ipv4/ip_forward').write_text('1')
def core_pids():
 result=[]
 for entry in pathlib.Path('/proc').iterdir():
  if not entry.name.isdigit():continue
  try:
   if entry.stat().st_uid==CORE_UID and (entry/'cmdline').read_bytes().split(b'\0')[0]==str(ROOT/'mihomo').encode():result.append(int(entry.name))
  except (OSError,ValueError):pass
 return result
def startcore():
 assert valid_lease(), 'Starlink service is not ready'
 try:
  pwd.getpwuid(CORE_UID);raise RuntimeError('Dedicated runtime UID is already assigned')
 except KeyError:pass
 assert not core_pids(),'Core is still running; stop it before retrying'
 runtime=ROOT/'runtime';runtime.mkdir(exist_ok=True);runtime.chmod(0o700);os.chown(runtime,CORE_UID,CORE_UID)
 ROOT.chmod(0o711)
 target=runtime/'config.yaml';shutil.copyfile(ROOT/'config.yaml',target);target.chmod(0o600);os.chown(target,CORE_UID,CORE_UID)
 def demote():os.setgroups([]);os.setgid(CORE_UID);os.setuid(CORE_UID)
 env={'PATH':'/usr/bin:/bin','HOME':str(runtime),'USER':'mihomo-c3'}
 (ROOT/'core.log').touch(exist_ok=True);(ROOT/'core.log').chmod(0o600)
 with (ROOT/'core.log').open('ab') as log:
  process=subprocess.Popen([str(ROOT/'mihomo'),'-d',str(runtime),'-f',str(target)],stdout=log,stderr=log,env=env,start_new_session=True,preexec_fn=demote)
 path=ROOT/'pid';path.write_text(str(process.pid));path.chmod(0o600);os.chown(path,1000,1000)
 # Popen returns before exec: do not report a launched PID until it is the core.
 deadline=time.monotonic()+5
 while time.monotonic()<deadline:
  if process.poll() is not None:raise RuntimeError('Core exited; check its private log')
  if process.pid in core_pids():
   start_watch(process.pid)
   return
  time.sleep(.05)
 raise RuntimeError('Core startup timed out')
def stopcore():
 stop_watch()
 # A failed early launch can leave a core whose PID is absent or stale.
 targets=core_pids()
 for pid in targets:
  try:os.kill(pid,signal.SIGTERM)
  except ProcessLookupError:pass
 deadline=time.monotonic()+4
 while time.monotonic()<deadline and set(targets)&set(core_pids()):time.sleep(.1)
 for pid in set(targets)&set(core_pids()):
  try:os.kill(pid,signal.SIGKILL)
  except ProcessLookupError:pass
 deadline=time.monotonic()+1
 while time.monotonic()<deadline and set(targets)&set(core_pids()):time.sleep(.05)
 assert not set(targets)&set(core_pids()),'Core did not stop'
 (ROOT/'pid').unlink(missing_ok=True)
def enable():
 try: _,network=hotspot()
 except (RuntimeError,AssertionError):network=None
 if network:run('ip','route','replace',network,'dev','wlan0','table',TABLE)
 run('ip','route','replace','default','dev',DEV,'table',TABLE)
 if network and 'iif wlan0' not in run('ip','rule','show').stdout:
  run('ip','rule','add','priority',PRIORITY,'iif','wlan0','lookup',TABLE)
 run(IPT,'-t','nat','-N',CHAIN,check=False);run(IPT,'-t','nat','-F',CHAIN)
 for protocol in ('udp','tcp'):run(IPT,'-t','nat','-A',CHAIN,'-p',protocol,'--dport','53','-j','REDIRECT','--to-ports','17893')
 rules=[['-t','nat','PREROUTING','-i','wlan0','-j',CHAIN],['-t','filter','FORWARD','-i','wlan0','-o',DEV,'-j','ACCEPT'],['-t','filter','FORWARD','-i',DEV,'-o','wlan0','-j','ACCEPT']] if network else []
 for rule in rules:
  prefix=rule[:2];rest=rule[2:]
  if run(IPT,*prefix,'-C',*rest,check=False).returncode:run(IPT,*prefix,'-I',*rest)
 for table,chain in [('mangle','C3MH_MARK'),('nat','C3MH_OUTDNS'),('filter','C3MH_INPUT')]:
  run(IPT,'-t',table,'-N',chain,check=False);run(IPT,'-t',table,'-F',chain)
 run(IPT,'-t','mangle','-A','C3MH_MARK','-m','owner','--uid-owner',str(CORE_UID),'-j','RETURN')
 for network in ['127.0.0.0/8','192.168.0.0/16','10.0.0.0/8','172.16.0.0/12','169.254.0.0/16','198.18.0.0/15','224.0.0.0/4','255.255.255.255/32']:
  run(IPT,'-t','mangle','-A','C3MH_MARK','-d',network,'-j','RETURN')
 run(IPT,'-t','mangle','-A','C3MH_MARK','-j','MARK','--set-mark','17890')
 run(IPT,'-t','nat','-A','C3MH_OUTDNS','-m','owner','--uid-owner',str(CORE_UID),'-j','RETURN')
 for protocol in ('udp','tcp'):run(IPT,'-t','nat','-A','C3MH_OUTDNS','-p',protocol,'--dport','53','-j','REDIRECT','--to-ports','17893')
 for interface in (('lo','wlan0') if network else ('lo',)):run(IPT,'-t','filter','-A','C3MH_INPUT','-i',interface,'-j','RETURN')
 for protocol in ('udp','tcp'):run(IPT,'-t','filter','-A','C3MH_INPUT','-p',protocol,'--dport','17893','-j','REJECT')
 for table,chain,parent in [('mangle','C3MH_MARK','OUTPUT'),('nat','C3MH_OUTDNS','OUTPUT'),('filter','C3MH_INPUT','INPUT')]:
  if run(IPT,'-t',table,'-C',parent,'-j',chain,check=False).returncode:run(IPT,'-t',table,'-I',parent,'-j',chain)
 rules=json.loads(run('ip','-j','rule').stdout)
 if not any(r.get('priority')==17880 and str(r.get('table'))==TABLE for r in rules):run('ip','rule','add','priority','17880','fwmark','17890/0xffff','lookup',TABLE)
 (ROOT/'gateway_enabled').write_text('1')
def disable():
 (ROOT/'gateway_enabled').unlink(missing_ok=True)
 run('ip','rule','del','priority',PRIORITY,'iif','wlan0','lookup',TABLE,check=False)
 run('ip','rule','del','priority','17880','fwmark','17890/0xffff','lookup',TABLE,check=False)
 for table,chain,parent in [('mangle','C3MH_MARK','OUTPUT'),('nat','C3MH_OUTDNS','OUTPUT'),('filter','C3MH_INPUT','INPUT')]:
  run(IPT,'-t',table,'-D',parent,'-j',chain,check=False);run(IPT,'-t',table,'-F',chain,check=False);run(IPT,'-t',table,'-X',chain,check=False)
 run('ip','route','flush','table',TABLE,check=False)
 for rule in [['-t','nat','PREROUTING','-i','wlan0','-j',CHAIN],['-t','filter','FORWARD','-i','wlan0','-o',DEV,'-j','ACCEPT'],['-t','filter','FORWARD','-i',DEV,'-o','wlan0','-j','ACCEPT']]:run(IPT,*rule[:2],'-D',*rule[2:],check=False)
 run(IPT,'-t','nat','-F',CHAIN,check=False);run(IPT,'-t','nat','-X',CHAIN,check=False)
 run('ip','link','del',DEV,check=False)
 state=ROOT/'gateway_state.json'
 if state.exists():
  pathlib.Path('/proc/sys/net/ipv4/ip_forward').write_text(json.loads(state.read_text())['previous_forward']);state.unlink()

def ticks(pid):
 return pathlib.Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]

def lease():
 try:return json.loads((ROOT/'starlink-lease.json').read_text())
 except (OSError,ValueError):return {}

def valid_lease(expected=None):
 state=lease() if expected is None else expected
 try:
  pid=int(state['pid'])
  return pathlib.Path(f'/proc/{pid}').stat().st_uid==1000 and ticks(pid)==state['start'] and b'starlink.service' in pathlib.Path(f'/proc/{pid}/cmdline').read_bytes()
 except (OSError,ValueError,KeyError):return False

def stop_watch():
 try:
  pid=int((ROOT/'starlink-watch.pid').read_text())
  if pathlib.Path(f'/proc/{pid}').stat().st_uid!=0 or b'starlink-watch' not in pathlib.Path(f'/proc/{pid}/cmdline').read_bytes():return
  os.kill(pid,signal.SIGTERM)
  deadline=time.monotonic()+2
  while pathlib.Path(f'/proc/{pid}').exists() and time.monotonic()<deadline:time.sleep(.05)
  if pathlib.Path(f'/proc/{pid}').exists():os.kill(pid,signal.SIGKILL)
 except (OSError,ValueError):pass
 finally:(ROOT/'starlink-watch.pid').unlink(missing_ok=True)

def start_watch(core_pid):
 fd=os.open(__file__,os.O_RDONLY)
 try:
  with (ROOT/'watch.log').open('ab') as log:
   p=subprocess.Popen(['/usr/bin/python3',f'/proc/self/fd/{fd}','watch','starlink-watch',str(core_pid),ticks(core_pid)],
                      pass_fds=(fd,),stdout=log,stderr=log,start_new_session=True)
  (ROOT/'watch.log').chmod(0o600)
  (ROOT/'starlink-watch.pid').write_text(str(p.pid))
 finally:os.close(fd)

def watch():
 core_pid=int(sys.argv[3]);started=sys.argv[4];parent=lease();stopped=False
 def explicit_stop(*_):
  nonlocal stopped
  stopped=True
 signal.signal(signal.SIGTERM,explicit_stop)
 signal.signal(signal.SIGINT,explicit_stop)
 def same_core():
  try:return core_pid in core_pids() and ticks(core_pid)==started
  except OSError:return False
 while not stopped and same_core() and valid_lease(parent):time.sleep(.5)
 if stopped:return
 # The daemon/core died. Restore ordinary routing instead of leaving a blackhole.
 if same_core():
  try:os.kill(core_pid,signal.SIGTERM)
  except ProcessLookupError:pass
  deadline=time.monotonic()+1
  while same_core() and time.monotonic()<deadline:time.sleep(.05)
  if same_core():
   try:os.kill(core_pid,signal.SIGKILL)
   except ProcessLookupError:pass
 try:current=int((ROOT/'pid').read_text())
 except (OSError,ValueError):current=None
 if current==core_pid or not core_pids():
  disable()
  (ROOT/'pid').unlink(missing_ok=True)

if __name__=='__main__':
 os.umask(0o077)
 assert os.geteuid()==0 and pathlib.Path('/AGNOS').exists(), 'AGNOS root helper required'
 action=sys.argv[1]
 try:
  if action in ('prepare','startcore','enable'):
   assert pathlib.Path('/data/params/d/IsOffroad').read_text().strip()=='1', 'Park before changing the VPN'
   assert not pathlib.Path('/data/params/d/IsEngaged').exists() or pathlib.Path('/data/params/d/IsEngaged').read_text().strip()!='1', 'Disengage before changing the VPN'
  actions={'prepare':prepare,'startcore':startcore,'stopcore':stopcore,'enable':enable,'disable':disable,'watch':watch}
  actions[action]()
  if action!='watch':print(json.dumps({'ok':True}))
 except Exception:
  # Do not echo arbitrary command stderr, config fragments or credentials.
  print(json.dumps({'error':'VPN gateway operation failed: '+action}))
  sys.exit(1)
