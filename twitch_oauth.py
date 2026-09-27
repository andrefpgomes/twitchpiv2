#!/usr/bin/env python3
import json, os, urllib.parse, urllib.request, urllib.error
BASE='/opt/twitch-pi'; ENV=BASE+'/config.env'
TOKEN_URL='https://id.twitch.tv/oauth2/token'; DEVICE_URL='https://id.twitch.tv/oauth2/device'; VALIDATE_URL='https://id.twitch.tv/oauth2/validate'

def read_env():
    out={}
    try:
        with open(ENV,encoding='utf-8') as f:
            for line in f:
                line=line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k,v=line.split('=',1); out[k]=v.strip().strip('"\'')
    except FileNotFoundError: pass
    return out

def write_env(values):
    os.makedirs(BASE,exist_ok=True); cur=read_env(); cur.update({k:v for k,v in values.items() if v is not None})
    tmp=ENV+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f:
        for k,v in cur.items(): f.write(f'{k}={v}\n')
    os.replace(tmp,ENV); os.chmod(ENV,0o600)

def client_id(): return read_env().get('TWITCH_CLIENT_ID','').strip()

def validate():
    env=read_env(); cid=env.get('TWITCH_CLIENT_ID',''); tok=env.get('TWITCH_OAUTH_TOKEN','')
    if not cid: return {'ok':False,'configured':False,'error':'TWITCH_CLIENT_ID não configurado.'}
    if not tok: return {'ok':False,'configured':False,'error':'Twitch ainda não foi autenticada.'}
    req=urllib.request.Request(VALIDATE_URL,headers={'Authorization':'OAuth '+tok})
    try:
        with urllib.request.urlopen(req,timeout=10) as r: data=json.load(r)
        if data.get('client_id') != cid: return {'ok':False,'configured':False,'error':'O token pertence a outro Client ID.'}
        return {'ok':True,'configured':True,'login':data.get('login'),'user_id':data.get('user_id'),'expires_in':data.get('expires_in')}
    except Exception: return {'ok':False,'configured':False,'error':'Token inválido ou expirado.'}

def start_device():
    cid=client_id()
    if not cid: raise RuntimeError('Configure primeiro o Twitch Client ID no painel.')
    data=urllib.parse.urlencode({'client_id':cid}).encode()
    req=urllib.request.Request(DEVICE_URL,data=data,headers={'Content-Type':'application/x-www-form-urlencoded'},method='POST')
    with urllib.request.urlopen(req,timeout=10) as r: return json.load(r)

def poll(device_code):
    cid=client_id(); data=urllib.parse.urlencode({'client_id':cid,'device_code':device_code,'grant_type':'urn:ietf:params:oauth:grant-type:device_code'}).encode()
    req=urllib.request.Request(TOKEN_URL,data=data,headers={'Content-Type':'application/x-www-form-urlencoded'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=10) as r: d=json.load(r)
    except urllib.error.HTTPError as e:
        try: d=json.loads(e.read().decode())
        except Exception: d={}
        return {'ok':False,'status':d.get('message','authorization_pending')}
    if 'access_token' in d:
        write_env({'TWITCH_OAUTH_TOKEN':d['access_token'],'TWITCH_REFRESH_TOKEN':d.get('refresh_token','')})
        return {'ok':True,'status':'authorized','expires_in':d.get('expires_in')}
    return {'ok':False,'status':d.get('message','authorization_pending')}
