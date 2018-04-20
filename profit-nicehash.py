#!/usr/bin/env python2.7

from __future__ import print_function
import json
import urllib2
import sys
import datetime
import time
import subprocess
import os

# load config

cfg=json.loads(open(sys.argv[1]).read())

miners=cfg["miners"]
user_name=cfg["user_name"]
miner_name=cfg["miner_name"]
currency=cfg["currency"]
pwrcost=cfg["pwrcost"]
min_profit=cfg["min_profit"]
algo_nicehash=["Scrypt","SHA256","Scryptntf","X11","X13","Keccak","X15","Nist5","NeoScrypt","Lyra2RE","Whirlpoolx","Qubit","Quark","Axiom","Lyra2RE2","Scryptjanenfl16","Blake256r8","Blake256r14","Blake256r8vnl","Hodl","Ethash","Decred","Cryptonight","Lbry","Equihash","Pascal","X11Gost","Sia","Blake2s","Skunk"]

os.environ["DISPLAY"]=":0"

# grab something from a website

def fetch(url):
  r=urllib2.Request(url)
  r.add_header("User-Agent", "Lynx/2.8.8dev.3 libwww-FM/2.14 SSL-MM/1.4.1")
  r.add_header("Pragma", "no-cache")
  return urllib2.build_opener().open(r).read()

# main

exchrate=float(json.loads(urllib2.urlopen("https://blockchain.info/ticker").read())[currency]["last"])
data_nicehash=json.loads(fetch("https://api.nicehash.com/api?method=simplemultialgo.info"))["result"]["simplemultialgo"]
coins_nicehash={}
for j in reversed(data_nicehash):
  try:
    miner=miners[algo_nicehash[j["algo"]]]
    coins_nicehash[j["name"]]=miner["bin"].format(HOST=algo_nicehash[j["algo"]].lower()+"."+"eu.nicehash.com", PORT=str(j["port"]), NAME=user_name, MINER=miner_name)
  except:
    data_nicehash.remove(j)

sort_nicehash={}
for j in data_nicehash:
  sort_nicehash[j["name"]+" ("+algo_nicehash[j["algo"]]+")"]=float(j["paying"])*miners[algo_nicehash[j["algo"]]]["speed"]-24.0*miners[algo_nicehash[j["algo"]]]["power"]*pwrcost/exchrate
sort_nicehash=sorted(sort_nicehash.items(), key=lambda x:x[1], reverse=True)
log=open("current-profit-nicehash", "w")
for j in sort_nicehash:
  log.write(j[0]+": "+format(j[1], ".8f")+" BTC/day ("+format(j[1]*exchrate, ".2f")+" "+currency+"/day)\n")
log.close()

max_profit_val=0 # find the most profitable coin
for i in data_nicehash:
  if float(i["paying"])*miners[algo_nicehash[i["algo"]]]["speed"]-24.0*miners[algo_nicehash[i["algo"]]]["power"]*pwrcost/exchrate>max_profit_val:
    max_profit=i
    max_profit_val=float(i["paying"])*miners[algo_nicehash[i["algo"]]]["speed"]-24.0*miners[algo_nicehash[i["algo"]]]["power"]*pwrcost/exchrate
miner=miners[algo_nicehash[i["algo"]]]
coin=coins_nicehash[max_profit["name"]]

# see if miner's already running

try:
  subprocess.check_output(["pgrep", "-f", "^"+coin.replace("+", "\\+")])
  current=1

except:
  current=0
if (current==0):
  other=0
  for algo in coins_nicehash:
    try:
      subprocess.check_output(["pgrep", "-f", "^"+coins_nicehash[algo].replace("+", "\\+")])
      other=1
    except:
      pass

if (current==0):
  # log a change
  algo_log=open("algo-log", "a")
  algo_log.write(str(datetime.datetime.now())+": "+max_profit["name"]+" ("+algo_nicehash[max_profit["algo"]]+") "+format(max_profit_val, ".8f")+" "+format(max_profit_val*exchrate, ".2f")+"\n")
  algo_log.close()
  if (other==1):
    # kill existing miners
    for algo in coins_nicehash:
       subprocess.call(["pkill", "-f", "^"+coins_nicehash[algo].replace("+", "\\+")])
    time.sleep(3)
  # launch new miner
  subprocess.call(("screen -dmS miner "+coin).split(" "))

