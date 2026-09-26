#!/usr/bin/env python3
import json, os, re, subprocess, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
BASE='/opt/twitch-pi'; PORT=int(os.environ.get('PORT','8765')); STATE_FILE=os.environ.get('STATE_FILE',BASE+'/state.json'); WEB=BASE+'/web'; PROFILE=os.environ.get('TWITCH_PROFILE',os.path.expanduser('~/.config/twitch-pi-chromium')); CHANNEL_RE=re.compile(r'^[A-Za-z0-9_]{1,30}$')
def load_state():
 s={'channel':'','status':'stopped','last_changed':None,'favorites':[]}
 try:
  with open(STATE_FILE,encoding='utf-8') as f:s.update(json.load(f))
 except Exception:pass
 s.setdefault('favorites',[]);return s
def save_state(s):
 os.makedirs(os.path.dirname(STATE_FILE),exist_ok=True); t=STATE_FILE+'.tmp'
 with open(t,'w',encoding='utf-8') as f:json.dump(s,f,ensure_ascii=False,indent=2)
 os.replace(t,STATE_FILE)
def chromium():
 for x in ('chromium','chromium-browser'):
  if subprocess.call(['bash','-lc',f'command -v {x} >/dev/null 2>&1'])==0:return x
 return None
def stop_chromium():subprocess.run(['pkill','-f',f'--user-data-dir={PROFILE}'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def start_chromium(url):
 c=chromium()
 if not c:raise RuntimeError('Chromium não está instalado.')
 os.makedirs(PROFILE,exist_ok=True);subprocess.Popen([c,f'--user-data-dir={PROFILE}','--no-first-run','--noerrdialogs','--disable-session-crashed-bubble','--disable-infobars',url],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def respond(h,code,obj):
 d=json.dumps(obj,ensure_ascii=False).encode();h.send_response(code);h.send_header('Content-Type','application/json; charset=utf-8');h.send_header('Cache-Control','no-store');h.send_header('Access-Control-Allow-Origin','*');h.send_header('Content-Length',str(len(d)));h.end_headers();h.wfile.write(d)
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  p=urlparse(self.path).path
  if p=='/api/status':
   s=load_state();s['hostname']=os.uname().nodename;s['chromium']=chromium() is not None;s['server_time']=int(time.time());respond(self,200,s);return
  if p in ('/api/start','/api/stop','/api/login'):
   try:
    s=load_state()
    if p=='/api/start':
     c=s.get('channel','')
     if not CHANNEL_RE.fullmatch(c):raise RuntimeError('Nenhum canal Twitch válido está selecionado.')
     stop_chromium();time.sleep(1);start_chromium('https://www.twitch.tv/'+c);s['status']='playing';s['last_changed']=int(time.time())
    elif p=='/api/stop':stop_chromium();s['status']='stopped';s['last_changed']=int(time.time())
    else:
     c=chromium()
     if not c:raise RuntimeError('Chromium não está instalado.')
     os.makedirs(PROFILE,exist_ok=True);subprocess.Popen([c,f'--user-data-dir={PROFILE}','--no-first-run','--noerrdialogs','https://www.twitch.tv/login'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
     respond(self,200,{'ok':True,'message':'O login Twitch foi aberto no Chromium.'});return
    save_state(s);respond(self,200,s)
   except Exception as e:respond(self,400,{'error':str(e)})
   return
  if p=='/':p='/index.html'
  types={'/index.html':'text/html; charset=utf-8','/style.css':'text/css; charset=utf-8','/app.js':'application/javascript; charset=utf-8'}
  if p in types:
   try:d=open(WEB+p,'rb').read()
   except FileNotFoundError:self.send_error(404);return
   self.send_response(200);self.send_header('Content-Type',types[p]);self.send_header('Content-Length',str(len(d)));self.end_headers();self.wfile.write(d);return
  self.send_error(404)
 def do_POST(self):
  p=urlparse(self.path).path
  if p not in ('/api/channel','/api/favorite'):respond(self,404,{'error':'not found'});return
  try:
   n=int(self.headers.get('Content-Length','0'));body=json.loads(self.rfile.read(n) or b'{}');s=load_state();c=str(body.get('channel','')).strip()
   if p=='/api/channel':
    if not CHANNEL_RE.fullmatch(c):raise ValueError('Canal Twitch inválido.')
    s['channel']=c
   else:
    if not CHANNEL_RE.fullmatch(c):raise ValueError('Canal inválido.')
    f=s.get('favorites',[])
    if body.get('action')=='add' and c not in f:f.append(c)
    if body.get('action')=='remove':f=[x for x in f if x!=c]
    s['favorites']=f[:30]
   save_state(s);respond(self,200,s)
  except Exception as e:respond(self,400,{'error':str(e)})
if __name__=='__main__':save_state(load_state());ThreadingHTTPServer(('0.0.0.0',PORT),Handler).serve_forever()
