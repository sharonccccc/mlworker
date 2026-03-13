# from langfuse import Langfuse
# langfuse = Langfuse()
# from langfuse.decorators import observe,langfuse_context
import time
# from pocket.utils import CC, cexists

import asyncio, warnings, copy, time

class BaseNode:
    def __init__(self): self.params,self.successors={},{}
    def set_params(self,params): self.params=params
    def add_successor(self,node,action="default"):
        if action in self.successors: warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action]=node;return node
    def prep(self,shared): pass
    def exec(self,prep_res): pass
    def post(self,shared,prep_res,exec_res): pass
    def _exec(self,prep_res): return self.exec(prep_res)
    def _run(self,shared): p=self.prep(shared);e=self._exec(p);return self.post(shared,p,e)
    def run(self,shared): 
        if self.successors: warnings.warn("Node won't run successors. Use Flow.")  
        return self._run(shared)
    def __rshift__(self,other): return self.add_successor(other)
    def __sub__(self,action):
        if isinstance(action,str): return _ConditionalTransition(self,action)
        raise TypeError("Action must be a string")

class _ConditionalTransition:
    def __init__(self,src,action): self.src,self.action=src,action
    def __rshift__(self,tgt): return self.src.add_successor(tgt,self.action)

class Node(BaseNode):
    def __init__(self,max_retries=1,wait=0): super().__init__();self.max_retries,self.wait=max_retries,wait
    def exec_fallback(self,prep_res,exc): raise exc
    # @observe
    def _exec(self,prep_res):
        # print(self.__class__.__name__)
        time.sleep(0.001)
        #cc = CC("123",timeout =(5, 5))
        #print(cc)
        # cc = cexists()
        # if cc:
        #     print("cancelled")
        #     raise Exception("cancelled")
        # langfuse_context.update_current_observation(name=self.__class__.__name__)
        for self.cur_retry in range(self.max_retries):
            try: return self.exec(prep_res)
            except Exception as e:
                if self.cur_retry==self.max_retries-1: return self.exec_fallback(prep_res,e)
                if self.wait>0: time.sleep(self.wait)
                    
class BatchNode(Node):
    def _exec(self,items): return [super(BatchNode,self)._exec(i) for i in (items or [])]

class Flow(BaseNode):
    def __init__(self,start): super().__init__();self.start=start
    def get_next_node(self,curr,action):
        nxt=curr.successors.get(action or "default")
        # if not nxt and curr.successors: warnings.warn(f"Flow ends: '{action}' not found in {list(curr.successors)}")
        return nxt
    def _orch(self,shared,params=None):
        curr,p=copy.copy(self.start),(params or {**self.params})
        while curr: curr.set_params(p);c=curr._run(shared);curr=copy.copy(self.get_next_node(curr,c))
    def _run(self,shared): pr=self.prep(shared);self._orch(shared);return self.post(shared,pr,None)
    def exec(self,prep_res): raise RuntimeError("Flow can't exec.")

class BatchFlow(Flow):
    def _run(self,shared):
        pr=self.prep(shared) or []
        for bp in pr: self._orch(shared,{**self.params,**bp})
        return self.post(shared,pr,None)

class AsyncNode(Node):
    def prep(self,shared): raise RuntimeError("Use prep_async.")
    def exec(self,prep_res): raise RuntimeError("Use exec_async.")
    def post(self,shared,prep_res,exec_res): raise RuntimeError("Use post_async.")
    def exec_fallback(self,prep_res,exc): raise RuntimeError("Use exec_fallback_async.")
    def _run(self,shared): raise RuntimeError("Use run_async.")
    async def prep_async(self,shared): pass
    async def exec_async(self,prep_res): pass
    async def exec_fallback_async(self,prep_res,exc): raise exc
    async def post_async(self,shared,prep_res,exec_res): pass
    async def _exec(self,prep_res): 
        for i in range(self.max_retries):
            try: return await self.exec_async(prep_res)
            except Exception as e:
                if i==self.max_retries-1: return await self.exec_fallback_async(prep_res,e)
                if self.wait>0: await asyncio.sleep(self.wait)
    async def run_async(self,shared): 
        if self.successors: warnings.warn("Node won't run successors. Use AsyncFlow.")  
        return await self._run_async(shared)
    async def _run_async(self,shared): p=await self.prep_async(shared);e=await self._exec(p);return await self.post_async(shared,p,e)

class AsyncBatchNode(AsyncNode,BatchNode):
    async def _exec(self,items): return [await super(AsyncBatchNode,self)._exec(i) for i in items]

class AsyncParallelBatchNode(AsyncNode,BatchNode):
    async def _exec(self,items): return await asyncio.gather(*(super(AsyncParallelBatchNode,self)._exec(i) for i in items))

class AsyncFlow(Flow,AsyncNode):
    async def _orch_async(self,shared,params=None):
        curr,p=copy.copy(self.start),(params or {**self.params})
        while curr:curr.set_params(p);c=await curr._run_async(shared) if isinstance(curr,AsyncNode) else curr._run(shared);curr=copy.copy(self.get_next_node(curr,c))
    async def _run_async(self,shared): p=await self.prep_async(shared);await self._orch_async(shared);return await self.post_async(shared,p,None)

class AsyncBatchFlow(AsyncFlow,BatchFlow):
    async def _run_async(self,shared):
        pr=await self.prep_async(shared) or []
        for bp in pr: await self._orch_async(shared,{**self.params,**bp})
        return await self.post_async(shared,pr,None)

class AsyncParallelBatchFlow(AsyncFlow,BatchFlow):
    async def _run_async(self,shared):
        pr=await self.prep_async(shared) or []
        await asyncio.gather(*(self._orch_async(shared,{**self.params,**bp}) for bp in pr))
        return await self.post_async(shared,pr,None)


def EXEC(flow,docs,shared,doc):
    if doc:
        return {
            "flow":build_mermaid(start=flow),
            "docs":docs
        }
    else:
        flow.run(shared)
        # trace_id = langfuse_context.get_current_trace_id()
        # shared["trace_id"] = trace_id
        return shared
##
def clean_subgraphs(mermaid_str: str) -> str:
    lines = mermaid_str.splitlines()
    cleaned_lines = []

    subgraph_level = 0  # 目前subgraph層級
    in_flowchart_header = False

    for line in lines:
        stripped = line.strip()

        # 保留 Mermaid 的 header，例如 flowchart TD 等
        if stripped.startswith("flowchart"):
            cleaned_lines.append(line)
            in_flowchart_header = True
            continue

        # subgraph開始
        if stripped.startswith("subgraph "):
            subgraph_level += 1
            if subgraph_level == 1:
                cleaned_lines.append(line)  # 只保留最外層subgraph
            continue

        # subgraph結束
        if stripped == "end":
            if subgraph_level == 1:
                cleaned_lines.append(line)
            subgraph_level -= 1
            continue

        # 只保留最外層 subgraph 內的內容
        if subgraph_level == 1:
            cleaned_lines.append(line)
        # 若 subgraph_level == 0 且不是 header，則跳過所有內容

    return "\n".join(cleaned_lines)


import re
def merge_subflows(flowchart):
    # 取得最外層 subgraph 的內容
    outer_subgraph_match = re.search(r'subgraph\s+subFlow\[.*?\](.*)end', flowchart, re.S)
    if not outer_subgraph_match:
        # 若沒有匹配到 subFlow，則直接回傳原內容
        return flowchart
    outer_content = outer_subgraph_match.group(1).strip()

    # 判斷是否存在巢狀子流程 subgraph（是否有 'subgraph sub' 開頭）
    if not re.search(r'subgraph\s+sub[^[]+\[', outer_content):
        # 若沒有子流程，代表為一般節點流程，不需拆分，保持原結構，只把subFlow改名為Flow即可
        # 這裡僅簡單替換 subgraph 名稱
        return re.sub(r'subgraph\s+subFlow', 'subgraph Flow', flowchart)

    # 若存在子流程，則執行拆分與合併邏輯

    # 取得所有子流程 subgraph 與其他頂層節點／連線
    subgraphs = re.findall(r'(subgraph\s+sub[^[]+\[.*?\].*?end)', outer_content, re.S)
    other_lines = re.sub(r'subgraph\s+sub[^[]+\[.*?\].*?end', '', outer_content, flags=re.S).strip().splitlines()

    # 清理空白行與多餘空格
    other_lines = [line.strip() for line in other_lines if line.strip()]

    # 收集所有子流程中的節點標籤，避免頂層出現重複節點
    subflow_labels = set()
    for sg in subgraphs:
        # 找出子流程內部的節點定義，格式類似 N3@{ label: 'sub_One' }
        nodes_in_sg = re.findall(r'\w+@\{\s*label:\s*\'([^\']+)\'\s*\}', sg)
        for label in nodes_in_sg:
            subflow_labels.add(label)

    # 過濾頂層節點中，標籤已存在於子流程 labels 的節點（即重覆節點）
    filtered_lines = []
    for line in other_lines:
        m = re.match(r'(\w+)@\{\s*label:\s*\'([^\']+)\'\s*\}', line)
        if m:
            label = m.group(2)
            if label in subflow_labels:
                continue
        filtered_lines.append(line)

    # 將頂層連線關係與剩餘節點分開
    connections = []
    nodes = []
    for line in filtered_lines:
        if '--' in line:
            connections.append(line)
        else:
            nodes.append(line)

    # 建立輸出內容
    output = ['flowchart TD']
    # 輸出所有子流程子圖
    for sg in subgraphs:
        output.append(sg.strip())
    # 父流程 subgraph，名稱改為 Flow
    output.append('subgraph Flow')
    for node in nodes:
        output.append(f'    {node}')

    # 將子流程作為節點連接至父流程的某節點（這裡按你給的範例，固定連接到N5）
    sub_names = []
    for sg in subgraphs:
        name_match = re.match(r'subgraph\s+(sub[^[]+)\["([^"]+)"\]', sg)
        if name_match:
            sub_names.append((name_match.group(1), name_match.group(2)))

    if len(sub_names) >= 2:
        output.append(f'    {sub_names[0][0]}["{sub_names[0][1]}"] --> N5 --> {sub_names[1][0]}["{sub_names[1][1]}"]')
    else:
        for sn in sub_names:
            output.append(f'    {sn[0]}["{sn[1]}"] --> N5')

    # 保留頂層原有連線關係中，仍存在節點的連線（簡單過濾）
    existing_nodes = set()
    for line in nodes:
        n = re.match(r'(\w+)@', line)
        if n:
            existing_nodes.add(n.group(1))
    filtered_connections = []
    for conn in connections:
        nodes_in_conn = re.findall(r'(\w+)', conn)
        if len(nodes_in_conn) >= 2 and all(n in existing_nodes for n in nodes_in_conn[:2]):
            filtered_connections.append(conn)
    for conn in filtered_connections:
        output.append(f'    {conn}')

    output.append('end')

    return '\n'.join(output)


def build_mermaid(start, subgraph=True):
    ids = {}
    visited = set()
    lines = ["flowchart TD"]
    ctr = 1
    flow_ctr = 0
    INDENT = "  "

    def get_id(n):
        nonlocal ctr
        if n in ids:
            return ids[n]
        nid = f"N{ctr}"
        ids[n] = nid
        ctr += 1
        return nid

    flow_names = {}

    def get_flow_name(node):
        nonlocal flow_ctr
        if node not in flow_names:
            # 若有 Name 屬性且不為空，則優先使用
            name = getattr(node, "Name", None)
            if name:
                flow_names[node] = str(name)
            else:
                if flow_ctr == 0:
                    flow_names[node] = "Flow"
                else:
                    flow_names[node] = f"Flow{flow_ctr}"
                flow_ctr += 1
        return flow_names[node]

    def walk(node, level=1, is_top=True):
        indent = INDENT * level
        nid = get_id(node)

        if node in visited:
            return
        visited.add(node)

        if isinstance(node, Flow):
            label = get_flow_name(node)
            if is_top:
                lines.append(f"{indent}subgraph sub{label}[\"{label}\"]")
            else:
                lines.append(f"{indent}{nid}@{{ label: '{label}' }}")
                lines.append(f"{indent}subgraph sub{label}[\"{label}\"]")

            if node.start:
                walk_subtree(node.start, level + 1)
            lines.append(f"{indent}end")

            for action, succ in node.successors.items():
                if succ != node.start:
                    walk_subtree(succ, level)
                    lines.append(f"{indent}{nid} -- {action} --> {get_id(succ)}")

        else:
            lines.append(f"{indent}{nid}@{{ label: '{type(node).__name__}' }}")
            for action, succ in node.successors.items():
                walk_subtree(succ, level)
                lines.append(f"{indent}{nid} -- {action} --> {get_id(succ)}")

    def walk_subtree(node, level):
        walk(node, level, is_top=False)

    walk(start, level=1, is_top=True)
    mermaid_str =  "\n".join(lines)
    if not subgraph:
      return clean_subgraphs(mermaid_str)
    return merge_subflows(mermaid_str)
    #return mermaid_str

# def build_mermaid(start,subgraph=True):
#     ids = {}
#     visited = set()
#     lines = ["flowchart TD"]
#     ctr = 1
#     flow_ctr = 0
#     INDENT = "  "

#     def get_id(n):
#         nonlocal ctr
#         if n in ids:
#             return ids[n]
#         nid = f"N{ctr}"
#         ids[n] = nid
#         ctr += 1
#         return nid

#     flow_names = {}

#     def get_flow_name(node):
#         nonlocal flow_ctr
#         if node not in flow_names:
#             if flow_ctr == 0:
#                 flow_names[node] = "Flow"
#             else:
#                 flow_names[node] = f"Flow{flow_ctr}"
#             flow_ctr += 1
#         return flow_names[node]

#     def walk(node, level=1, is_top=True):
#         indent = INDENT * level
#         nid = get_id(node)

#         if node in visited:
#             return
#         visited.add(node)

#         if isinstance(node, Flow):
#             label = get_flow_name(node)
#             if is_top:
#                 # 最上層 Flow 僅產生 subgraph，不會另外建立節點
#                 lines.append(f"{indent}subgraph sub{flow_names[node]}[\"{label}\"]")
#             else:
#                 # 子 Flow 會先建立節點標籤，再建立 subgraph
#                 lines.append(f"{indent}{nid}@{{ label: '{label}' }}")
#                 lines.append(f"{indent}subgraph sub{flow_names[node]}[\"{label}\"]")

#             if node.start:
#                 walk_subtree(node.start, level + 1)
#             lines.append(f"{indent}end")

#             for action, succ in node.successors.items():
#                 if succ != node.start:
#                     walk_subtree(succ, level)
#                     lines.append(f"{indent}{nid} -- {action} --> {get_id(succ)}")

#         else:
#             lines.append(f"{indent}{nid}@{{ label: '{type(node).__name__}' }}")
#             for action, succ in node.successors.items():
#                 walk_subtree(succ, level)
#                 lines.append(f"{indent}{nid} -- {action} --> {get_id(succ)}")

#     def walk_subtree(node, level):
#         walk(node, level, is_top=False)

#     walk(start, level=1, is_top=True)
#     mermaid_str =  "\n".join(lines)
#     if not subgraph:
#       return clean_subgraphs(mermaid_str)
#     return mermaid_str


# def build_mermaid(start):
#     ids = {}
#     visited = set()
#     lines = ["flowchart TD"]
#     ctr = 1
#     flow_ctr = 0
#     INDENT = "  "

#     def get_id(n):
#         nonlocal ctr
#         if n in ids:
#             return ids[n]
#         nid = f"N{ctr}"
#         ids[n] = nid
#         ctr += 1
#         return nid

#     flow_names = {}

#     def get_flow_name(node):
#         nonlocal flow_ctr
#         if node not in flow_names:
#             if flow_ctr == 0:
#                 flow_names[node] = "Flow"
#             else:
#                 flow_names[node] = f"Flow{flow_ctr}"
#             flow_ctr += 1
#         return flow_names[node]

#     def walk(node, level=1):
#         indent = INDENT * level
#         nid = get_id(node)

#         if node in visited:
#             return
#         visited.add(node)

#         if isinstance(node, Flow):
#             label = get_flow_name(node)
#             lines.append(f"{indent}{nid}@{{ label: '{label}' }}")
#             sub_name = f"sub{flow_names[node]}"
#             lines.append(f"{indent}subgraph {sub_name}[\"{label}\"]")
#             if node.start:
#                 walk_subtree(node.start, level + 1)
#             lines.append(f"{indent}end")

#             for action, succ in node.successors.items():
#                 if succ != node.start:
#                     walk_subtree(succ, level)
#                     lines.append(f"{indent}{nid} -- {action} --> {get_id(succ)}")

#         else:
#             lines.append(f"{indent}{nid}@{{ label: '{type(node).__name__}' }}")
#             for action, succ in node.successors.items():
#                 walk_subtree(succ, level)
#                 lines.append(f"{indent}{nid} -- {action} --> {get_id(succ)}")

#     def walk_subtree(node, level):
#         nid = get_id(node)
#         indent = INDENT * level
#         if node in visited:
#             return
#         visited.add(node)

#         if isinstance(node, Flow):
#             label = get_flow_name(node)
#             lines.append(f"{indent}{nid}@{{ label: '{label}' }}")
#             sub_name = f"sub{flow_names[node]}"
#             lines.append(f"{indent}subgraph {sub_name}[\"{label}\"]")
#             if node.start:
#                 walk_subtree(node.start, level + 1)
#             lines.append(f"{indent}end")

#             for action, succ in node.successors.items():
#                 if succ != node.start:
#                     walk_subtree(succ, level)
#                     lines.append(f"{indent}{nid} -- {action} --> {get_id(succ)}")

#         else:
#             lines.append(f"{indent}{nid}@{{ label: '{type(node).__name__}' }}")
#             for action, succ in node.successors.items():
#                 walk_subtree(succ, level)
#                 lines.append(f"{indent}{nid} -- {action} --> {get_id(succ)}")

#     walk(start)
#     return "\n".join(lines)


class ObservableShare(dict):
    def __init__(self, *args, **kwargs):
        self._callback = kwargs.pop("callback", None)
        super().__init__(*args, **kwargs)

    def _trigger_callback(self):
        if self._callback:
            self._callback(self)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._trigger_callback()

    def __delitem__(self, key):
        super().__delitem__(key)
        self._trigger_callback()

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self._trigger_callback()

    def clear(self):
        super().clear()
        self._trigger_callback()

    def pop(self, key, default=None):
        result = super().pop(key, default)
        self._trigger_callback()
        return result

    def popitem(self):
        result = super().popitem()
        self._trigger_callback()
        return result