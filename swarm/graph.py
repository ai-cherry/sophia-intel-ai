from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from rag.pipeline import rag_tool
from integrations.mcp_tools import mcp_learn
import os, json, time

# Optional No-BS filter
try:
    from scripts.tone_filter import enforce as _enforce
except Exception:
    _enforce = lambda x: x

class S(TypedDict, total=False):
    query: str
    stage: int            # 0..4 (architect=0, builder=1, tester=2, operator=3, done=4)
    artifacts: Dict[str, Any]
    hops: int
    stage_history: List[str]
    error_count: int
    start_time: float

STAGES = ["architect","builder","tester","operator"]
MAX_HOPS = int(os.getenv("MAX_SWARM_HOPS", "12"))
MAX_STAGE_TIME = int(os.getenv("MAX_STAGE_TIME_MINUTES", "10")) * 60

def _llm():
    timeout = float(os.getenv("LLM_TIMEOUT", "45"))
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    
    base_url = os.getenv("OPENAI_BASE_URL")
    if os.getenv("OPENAI_API_KEY") or base_url:
        return ChatOpenAI(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            base_url=base_url,
            timeout=timeout,
            max_tokens=max_tokens,
            temperature=temperature,
            request_timeout=timeout,
            max_retries=2
        )
    
    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        temperature=temperature,
        timeout=timeout,
        num_predict=max_tokens
    )

LLM = _llm()
CKPT = MemorySaver()

def supervisor(s: S) -> S:
    current_time = time.time()
    s["hops"] = s.get("hops", 0) + 1
    s["error_count"] = s.get("error_count", 0)
    s["start_time"] = s.get("start_time", current_time)
    s["stage_history"] = s.get("stage_history", [])
    
    # Circuit breakers
    if s["hops"] > MAX_HOPS:
        s["stage"] = 4
        s.setdefault("artifacts", {})["supervisor_note"] = f"Terminated: exceeded {MAX_HOPS} hops"
        return s
    
    if current_time - s["start_time"] > MAX_STAGE_TIME:
        s["stage"] = 4  
        s.setdefault("artifacts", {})["supervisor_note"] = f"Terminated: exceeded {MAX_STAGE_TIME}s time limit"
        return s
        
    if s["error_count"] >= 3:
        s["stage"] = 4
        s.setdefault("artifacts", {})["supervisor_note"] = "Terminated: too many errors"
        return s
    
    current_stage = s.get("stage", 0)
    
    # Stage advancement logic with artifact validation
    if current_stage < 4:
        stage_name = STAGES[current_stage]
        artifacts = s.get("artifacts", {})
        
        # Check if current stage has produced valid artifact
        if (stage_name in artifacts and 
            artifacts[stage_name] and 
            len(artifacts[stage_name].strip()) > 50):  # Minimum artifact size
            current_stage += 1
            s["stage_history"].append(f"{stage_name}_completed")
        
    s["stage"] = current_stage
    return s

def _agent_with_monitoring(name: str, system_prompt: str):
    """Create agent with comprehensive error handling and monitoring"""
    
    def agent_fn(state: S) -> S:
        start_time = time.time()
        
        try:
            # Input validation
            if not state.get("query", "").strip():
                raise ValueError("Empty query provided")
            
            # Get context with timeout
            try:
                context = rag_tool(state["query"])
            except Exception as e:
                context = json.dumps({"error": f"RAG failed: {str(e)}"})
                state["error_count"] = state.get("error_count", 0) + 1
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nTask:\n{state['query']}"}
            ]
            
            # LLM call with retry logic
            max_retries = 3
            output = None
            
            for attempt in range(max_retries):
                try:
                    response = LLM.invoke(messages)
                    output = response.content
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2 ** attempt)
                    print(f"LLM retry {attempt + 1} for {name}: {e}")
            
            if not output:
                raise RuntimeError("LLM produced no output")
            
            # Apply limits and filters
            max_chars = int(os.getenv("MAX_ARTIFACT_CHARS", "25000"))
            output = output[:max_chars]
            
            # Apply tone filter if enabled
            if os.getenv("ROO_TONE") == "no_bs":
                try:
                    output = _enforce(output)
                except Exception:
                    pass
            
            # Validate output quality
            if len(output.strip()) < 50:
                raise ValueError(f"Output too short: {len(output)} chars")
            
            # Store artifact
            state.setdefault("artifacts", {})[name] = output
            
            duration = time.time() - start_time
            
            # Log success
            telemetry_event = {
                "agent": name,
                "event": "output",
                "len": len(output),
                "duration": duration,
                "context_len": len(context),
                "success": True
            }
            
            # MCP learning
            mcp_learn(telemetry_event)
            
            # Local telemetry
            try:
                from scripts.tail_handoffs import log
                log(telemetry_event)
            except Exception:
                pass
                
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)[:200]
            
            # Log error
            error_event = {
                "agent": name,
                "event": "error", 
                "error": error_msg,
                "duration": duration,
                "stage": state.get("stage", -1)
            }
            
            state["error_count"] = state.get("error_count", 0) + 1
            state.setdefault("artifacts", {})[f"{name}_error"] = error_msg
            
            try:
                from scripts.tail_handoffs import log
                log(error_event)
            except Exception:
                pass
            
            print(f"Agent {name} failed: {error_msg}")
        
        return state
    
    return agent_fn

def route_logic(s: S) -> str:
    stage = s.get("stage", 0)
    if stage >= 4:
        return "done"
    return STAGES[stage]

graph = StateGraph(S)
graph.add_node("supervisor", supervisor)
graph.add_node("architect", _agent_with_monitoring("architect", "You are a principal architect. Output a numbered plan and unified diff blocks only."))
graph.add_node("builder", _agent_with_monitoring("builder", "You are a senior builder. Output diffs + exact test commands."))
graph.add_node("tester", _agent_with_monitoring("tester", "You are QA. Output pytest files + run steps; no network."))
graph.add_node("operator", _agent_with_monitoring("operator", "You are DevOps. Output Pulumi preview steps; never apply."))

graph.add_edge(START, "supervisor")
for n in ["architect", "builder", "tester", "operator"]:
    graph.add_edge(n, "supervisor")

graph.add_conditional_edges("supervisor", route_logic, {
    "architect": "architect",
    "builder": "builder", 
    "tester": "tester",
    "operator": "operator",
    "done": END
})

app = graph.compile(checkpointer=CKPT)

def run(query: str) -> Dict[str, Any]:
    r = app.invoke({"query": query}, config={"configurable": {"thread_id": str(int(time.time()))}})
    return r.get("artifacts", {})
