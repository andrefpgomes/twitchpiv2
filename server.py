#!/usr/bin/env python3
import json, os, re, subprocess, time, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
BASE='/opt/twitch-pi'; PORT=int(os.environ.get('PORT','8765')); STATE_FILE=os.environ.get('STATE_FILE',BASE+'/state.json'); WEB=BASE+'/web'
TWITCH_USER=os.environ.get('TWITCH_USER','andre'); TWITCH_UID=os.environ.get('TWITCH_UID','1000'); PROFILE=os.environ.get('TWITCH_PROFILE',f'/home/{TWITCH_USER}/.config/twitch-pi-chromium')
CHANNEL_RE=re.compile(r'^[A-Za-z0-9_]{1,30}$'); GAME_RE=re.compile(r'^[A-Za-z0-9][A-Za-z0-9 ._\-]{0,60}$'); CLIENT_RE=re.compile(r'^[A-Za-z0-9]{20,60}$'); DROP_CACHE={'at':0,'data':None}; DEVICE={'code':None,'expires':0}

def load_state():
    s={'channel':'','status':'stopped','last_changed':None,'favorites':[]}
    try:
        with open(STATE_FILE,encoding='utf-8') as f:s.update(json.load(f))
    except Exception:pass
    s.setdefault('favorites',[]); return s

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
    os.makedirs(PROFILE,exist_ok=True); subprocess.run(['chown','-R',f'{TWITCH_USER}:{TWITCH_USER}',PROFILE],check=False)
    subprocess.Popen(['sudo','-u',TWITCH_USER,'env',f'DISPLAY=:0',f'WAYLAND_DISPLAY=wayland-0',f'XDG_RUNTIME_DIR=/run/user/{TWITCH_UID}',c,f'--user-data-dir={PROFILE}','--no-first-run','--noerrdialogs','--disable-session-crashed-bubble','--disable-infobars',url],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def drops_config():
    p=BASE+'/drops_config.json'
    try:
        with open(p,encoding='utf-8') as f:return json.load(f)
    except Exception:
        d={'games':[{'name':'Fortnite','slug':'fortnite','enabled':True},{'name':'Minecraft','slug':'minecraft','enabled':True},{'name':'Rocket League','slug':'rocket-league','enabled':True}]}; os.makedirs(BASE,exist_ok=True)
        with open(p,'w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
        return d

def save_drops_config(d):
    with open(BASE+'/drops_config.json.tmp','w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
    os.replace(BASE+'/drops_config.json.tmp',BASE+'/drops_config.json')

def get_drops():
    global DROP_CACHE
    if DROP_CACHE['data'] is not None and time.time()-DROP_CACHE['at']<60:return DROP_CACHE['data']
    try:
        if BASE not in sys.path:sys.path.insert(0,BASE)
        from drops_tracker import get
        data=get(); DROP_CACHE={'at':time.time(),'data':data}; return data
    except Exception as e:return {'ok':False,'error':str(e),'campaigns':[]}

def oauth():
    if BASE not in sys.path:sys.path.insert(0,BASE)
    import twitch_oauth
    return twitch_oauth

def respond(h,code,obj):
    d=json.dumps(obj,ensure_ascii=False).encode(); h.send_response(code); h.send_header('Content-Type','application/json; charset=utf-8'); h.send_header('Cache-Control','no-store'); h.send_header('Access-Control-Allow-Origin','*'); h.send_header('Content-Length',str(len(d))); h.end_headers(); h.wfile.write(d)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        global DEVICE
        p=urlparse(self.path).path
        if p=='/api/status':
            s=load_state(); s['hostname']=os.uname().nodename; s['chromium']=chromium() is not None; s['server_time']=int(time.time()); respond(self,200,s); return
        if p=='/api/drops':respond(self,200,get_drops());return
        if p=='/api/drops/games':respond(self,200,drops_config());return
        if p=='/api/auth/status':respond(self,200,oauth().validate());return
        if p=='/api/auth/start':
            try:
                d=oauth().start_device(); DEVICE={'code':d['device_code'],'expires':time.time()+d.get('expires_in',900)}
                respond(self,200,{'ok':True,'verification_uri':d.get('verification_uri_complete') or d.get('verification_uri'),'user_code':d.get('user_code'),'expires_in':d.get('expires_in',900),'interval':d.get('interval',5)})
            except Exception as e:respond(self,400,{'error':str(e)})
            return
        if p=='/api/auth/poll':
            try:
                if not DEVICE.get('code') or time.time()>DEVICE.get('expires',0):raise RuntimeError('A autorização expirou. Inicia novamente.')
                r=oauth().poll(DEVICE['code']);
                if r.get('ok'):DEVICE={'code':None,'expires':0}
                respond(self,200,r)
            except Exception as e:respond(self,400,{'error':str(e)})
            return
        if p in ('/api/start','/api/stop','/api/login'):
            try:
                s=load_state()
                if p=='/api/start':
                    c=s.get('channel','')
                    if not CHANNEL_RE.fullmatch(c):raise RuntimeError('Nenhum canal Twitch válido está selecionado.')
                    stop_chromium();time.sleep(1);start_chromium('https://www.twitch.tv/'+c);s['status']='playing';s['last_changed']=int(time.time())
                elif p=='/api/stop':stop_chromium();s['status']='stopped';s['last_changed']=int(time.time())
                else:
                    if not chromium():raise RuntimeError('Chromium não está instalado.')
                    start_chromium('https://www.twitch.tv/login');respond(self,200,{'ok':True,'message':'O login Twitch foi aberto no Chromium.'});return
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
        if p not in ('/api/channel','/api/favorite','/api/drops/games','/api/auth/client'):respond(self,404,{'error':'not found'});return
        try:
            n=int(self.headers.get('Content-Length','0'));body=json.loads(self.rfile.read(n) or b'{}')
            if p=='/api/auth/client':
                cid=str(body.get('client_id','')).strip()
                if not CLIENT_RE.fullmatch(cid):raise ValueError('Client ID Twitch inválido.')
                oauth().write_env({'TWITCH_CLIENT_ID':cid}); respond(self,200,{'ok':True,'message':'Client ID guardado localmente. Agora podes ligar a conta Twitch.'}); return
            if p=='/api/drops/games':
                name=str(body.get('name','')).strip()
                if not GAME_RE.fullmatch(name):raise ValueError('Nome de jogo inválido.')
                d=drops_config(); games=d.setdefault('games',[]); key=name.casefold()
                if not any(g.get('name','').casefold()==key for g in games):games.append({'name':name,'slug':re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-'),'enabled':True})
                save_drops_config(d); DROP_CACHE={'at':0,'data':None}; respond(self,200,d); return
            s=load_state();c=str(body.get('channel','')).strip()
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
