#!/usr/bin/env python3
"""Read-only Twitch Drops inventory tracker for TwitchPi v2."""
import json, os, time, urllib.request
BASE='/opt/twitch-pi'; CONFIG=BASE+'/drops_config.json'; ENV=BASE+'/config.env'; GQL='https://gql.twitch.tv/gql'
INVENTORY_HASHES=['e7197a7e03be13e423118005966d097a2f44045b3642bfdb70820e01c8129fd6','d86775d0ef16a63a33ad52e80eaff963b2d5b72fada7c991504a57496e1d8e4b','37fea486d6179047c41d0f549088a4c3a7dd60c05c70956a1490262f532dccd9']
DEFAULT={'games':[{'name':'Fortnite','slug':'fortnite','enabled':True},{'name':'Minecraft','slug':'minecraft','enabled':True},{'name':'Rocket League','slug':'rocket-league','enabled':True}]}

def load_config():
    try:
        with open(CONFIG,encoding='utf-8') as f:return json.load(f)
    except Exception:
        os.makedirs(BASE,exist_ok=True)
        with open(CONFIG,'w',encoding='utf-8') as f:json.dump(DEFAULT,f,ensure_ascii=False,indent=2)
        return DEFAULT

def token():
    try:
        for line in open(ENV,encoding='utf-8'):
            if line.strip().startswith('TWITCH_OAUTH_TOKEN='):return line.split('=',1)[1].strip().strip('"\'')
    except FileNotFoundError:pass
    return os.environ.get('TWITCH_OAUTH_TOKEN','').strip()

def query():
    tok=token()
    if not tok:return {'ok':False,'error':'TWITCH_OAUTH_TOKEN não configurado.','campaigns':[]}
    headers={'Content-Type':'application/json','Authorization':'OAuth '+tok,'Client-Id':os.environ.get('TWITCH_CLIENT_ID','kd1unb4b3q4t58fwlpcbzcbnm76a8fp'),'User-Agent':'TwitchPi/2.0','Origin':'https://www.twitch.tv','Referer':'https://www.twitch.tv'}
    for h in INVENTORY_HASHES:
        body={'operationName':'Inventory','variables':{'fetchRewardCampaigns':True},'extensions':{'persistedQuery':{'version':1,'sha256Hash':h}}}
        try:
            req=urllib.request.Request(GQL,data=json.dumps(body).encode(),headers=headers,method='POST')
            with urllib.request.urlopen(req,timeout=12) as r:data=json.load(r)
            inv=data.get('data',{}).get('currentUser',{}).get('inventory')
            if inv is not None:return normalize(inv)
        except Exception:continue
    return {'ok':False,'error':'Não foi possível obter o inventário de Drops da Twitch. O formato/hash da consulta pode ter mudado.','campaigns':[]}

def normalize(inv):
    wanted={g['name'].casefold() for g in load_config().get('games',[]) if g.get('enabled')}; out=[]
    for c in inv.get('dropCampaignsInProgress') or []:
        game=((c.get('game') or {}).get('name') or '').strip()
        if wanted and game.casefold() not in wanted:continue
        drops=[]
        for d in c.get('timeBasedDrops') or []:
            cur=(d.get('self') or {}).get('currentMinutesWatched',0) or 0; req=d.get('requiredMinutesWatched',0) or 0
            drops.append({'name':d.get('name','Drop'),'current':cur,'required':req,'percent':round(min(100,cur/req*100 if req else 0),1),'claimed':bool((d.get('self') or {}).get('isClaimed')),'rewards':[x.get('benefit',{}).get('name') for x in (d.get('benefitEdges') or []) if x.get('benefit')]})
        out.append({'id':c.get('id'),'name':c.get('name',''),'game':game,'status':c.get('status',''),'startAt':c.get('startAt'),'endAt':c.get('endAt'),'drops':drops})
    return {'ok':True,'updated_at':int(time.time()),'campaigns':out}

def get():return query()
if __name__=='__main__':print(json.dumps(get(),ensure_ascii=False,indent=2))
