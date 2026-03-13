from typing import TypedDict, Dict, Any, Optional

from langchain_core.prompts import PromptTemplate,ChatPromptTemplate

import os

socket_url = 'xxx'
invoke_url = 'xxx'

def GET(obj: dict, path: str, default: any = None) -> any:
    # Split the path and iterate through it
    keys = path.split(".")
    tmp = obj
    crt = []
    for key in keys:
        crt.append(key)
        # Handle if the current tmp is None or not a dict
        if tmp is None or not isinstance(tmp, dict):
            return default
        tmp = tmp.get(key, default)
        #print(tmp,".".join(crt))
        
    return tmp ,".".join(crt)

import json
import requests
import asyncio
import datetime

# from SSE import Live
import redis
redis_client = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
def redis_key(run_id: str, field:str = "data")-> str:
    return f"pocket:sub:{run_id}:{field}"

def Live(run_id:str,event:dict)->int:
     
    if run_id is None or run_id == "":
       return 0

    key_events = redis_key(run_id, "events")
    #print(key_events,'\r\n',event)
    return redis_client.rpush(key_events,json.dumps(event))
    
##BEGIN TOOLS
import aiohttp
async def sendSocket(runId,data,s,timeout, semaphore):
    #print("1PUSH",runId)
    async with semaphore:  # 使用 Semaphore（信號量）限制併發數量
        data['st'] = datetime.datetime.now().timestamp() 
        await asyncio.sleep(s)
        error = ""
        try:
            async with aiohttp.ClientSession() as client:
                response = await client.post( os.environ.get("socket_url",socket_url),
                                        data={'runId':runId,
                                        'json':json.dumps(data)})
            #print("3PUSH",runId)
        except requests.exceptions.ConnectTimeout:
            error = 'ConnectTimeout'
        except requests.exceptions.ReadTimeout:
            error = 'ReadTimeout'
            
    print("aPUSH",data['st'],runId,error)
    
def apush(runId,data,s = 0, timeout = (0.05, 0.3), semaphore = asyncio.Semaphore(3)):
    loop = asyncio.get_running_loop()
    tsk = loop.create_task(sendSocket(runId,data,s,timeout,semaphore))
    #await tsk

    
def push(runId,data,timeout =(0.05, 0.3) ):
    data["st"] = datetime.datetime.now().timestamp() 
    error = ""
    try:
        requests.post(url=os.environ.get("socket_url",socket_url),
                      data={'runId':runId,
                            'json':json.dumps(data)
                           },
                     timeout=timeout)
    except requests.exceptions.ConnectTimeout:
        error = 'ConnectTimeout'
    except requests.exceptions.ReadTimeout:
        error = 'ReadTimeout'
        
    print(" PUSH",data['st'],runId,error)

import importlib

async def Invoke(func,data,s,timeout,semaphore,pkg='tools'):
    async with semaphore:  # 使用 Semaphore（信號量）限制併發數量
        await asyncio.sleep(s)
        data['st'] = datetime.datetime.now().timestamp() 

        error = ""
        result = {}
        try:     
            async with aiohttp.ClientSession() as client:
                response = await client.post( os.environ.get("invoke_url",invoke_url),
                                        data={'func':func,
                                               'pkg': pkg,
                                        'args':json.dumps(data)})
                result = {
                    'ok':response.ok,
                    'status_code': response.status,
                    'json':await response.json(),
                    'text':await response.text(),
                }
                #print(result)
        except requests.exceptions.ConnectTimeout:
            error = 'ConnectTimeout'
        except requests.exceptions.ReadTimeout:
            error = 'ReadTimeout'
            
        print("aRUN",data['st'],func,error)
        return result

def aRun(func,data,s = 0, timeout = (0.5, 10), semaphore = asyncio.Semaphore(3),pkg='tools'):
    loop = asyncio.get_running_loop()
    tsk = loop.create_task(Invoke(func,data,s,timeout,semaphore,pkg))
    return tsk
    
def Run(func,data,timeout =(0.5, 10),pkg='tools' ):
    data["st"] = datetime.datetime.now().timestamp() 
    error = ""
    result = {}
    try:
        res = requests.post(url=os.environ.get("invoke_url",invoke_url),
                      data={'func':func,
                            'pkg': pkg,
                            'args':json.dumps(data)
                           },
                     timeout=timeout)
        result = res
    except requests.exceptions.ConnectTimeout:
        error = 'ConnectTimeout'
    except requests.exceptions.ReadTimeout:
        error = 'ReadTimeout'
        
    print(" RUN",data['st'],func,error)
    return result


from pathlib import Path

import time
import json
class PPrint:
    def __init__(self, interval_ms):
        """
        interval_ms: 最小間隔時間（毫秒）
        """
        self.interval = interval_ms / 1000.0  # 轉為秒
        self.last_print_time = time.time()

    def print(self, *args, **kwargs):
        now = time.time()
        elapsed = now - self.last_print_time

        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)

        print("[[[", *args, "]]]", **kwargs)
        self.last_print_time = time.time()    
        
    def json(self, dic):
        now = time.time()
        elapsed = now - self.last_print_time

        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)

        print("[[[", json.dumps(dic), "]]]")
        self.last_print_time = time.time()    


