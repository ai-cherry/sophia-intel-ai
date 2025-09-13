"use client"
import React, { useEffect, useMemo, useState } from 'react'

type Model = { id: string; provider: string; display?: string }
type ModelsResp = { aliases: Record<string,string>; models: Model[] }
type Msg = { role: 'user'|'assistant'|'system'; content: string; metaAgentRole?: string }

export default function StudioPage() {
  const [models, setModels] = useState<Model[]>([])
  const [aliases, setAliases] = useState<Record<string,string>>({})
  const [selected, setSelected] = useState<string>('claude-3-5-sonnet')
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [stream, setStream] = useState(false)
  const [activeAgentRole, setActiveAgentRole] = useState<string>('')
  const getModelForRole = (role: string) => {
    const row = profile.agents.find(a => a.role.toLowerCase() === role.toLowerCase())
    if (!row) return null
    return resolveAliasOrModel(row.aliasOrModel)
  }
  const [messages, setMessages] = useState<Msg[]>([])
  const [status, setStatus] = useState<{litellm:boolean;mcp:{memory:boolean;fs:boolean;git:boolean}}|null>(null)
  const [obs, setObs] = useState<{count?:number;p50?:number|null;p95?:number|null;models?:Record<string,number>}>({})
  // Context selections
  const [memQuery, setMemQuery] = useState('')
  const [memItems, setMemItems] = useState<string[]>([])
  const [memSelected, setMemSelected] = useState<string[]>([])
  const [fsPattern, setFsPattern] = useState('*.ts')
  const [fsFiles, setFsFiles] = useState<string[]>([])
  const [fsSelected, setFsSelected] = useState<{path:string;start?:number;end?:number}[]>([])
  const [fsSnippetPath, setFsSnippetPath] = useState<string>('')
  const [fsStart, setFsStart] = useState<string>('1')
  const [fsEnd, setFsEnd] = useState<string>('100')
  const [fsPreview, setFsPreview] = useState<string>('')
  const [fsPreviewLoading, setFsPreviewLoading] = useState(false)
  const [gitQuery, setGitQuery] = useState('className')
  const [gitResults, setGitResults] = useState<string[]>([])
  const [gitSelected, setGitSelected] = useState<string[]>([])
  // Profiles editor
  type AgentRow = { role: string; aliasOrModel: string; temperature: number; tools: string[] }
  type Profile = { name: string; agents: AgentRow[] }
  const [profile, setProfile] = useState<Profile>({ name: 'default', agents: [] })
  const [savingProfile, setSavingProfile] = useState(false)

  useEffect(() => {
    void (async () => {
      try {
        const r = await fetch('/api/models', { cache: 'no-store' })
        const d: ModelsResp = await r.json()
        setModels(d.models)
        setAliases(d.aliases)
        if (d.aliases?.claude) setSelected(d.aliases.claude)
      } catch {}
      try {
        const r = await fetch('/api/status', { cache: 'no-store' })
        const d = await r.json()
        setStatus({ litellm: !!d?.litellm?.ok, mcp: d?.mcp ?? {memory:false,fs:false,git:false} })
      } catch {}
      try {
        const r = await fetch('/api/observability', { cache: 'no-store' })
        const d = await r.json()
        if (d?.ok) setObs({ count:d.count, p50:d.p50??null, p95:d.p95??null, models:d.models||{} })
      } catch {}
    })()
  }, [])

  useEffect(() => {
    void (async () => {
      try {
        const r = await fetch('/api/agents/profile', { cache: 'no-store' })
        const d = await r.json()
        if (d?.ok && d?.profile) setProfile(d.profile)
      } catch {}
    })()
  }, [])

  const onSend = async () => {
    if (!input.trim()) return
    const newMsgs = [...messages, { role: 'user' as const, content: input }]
    setMessages(newMsgs)
    setInput('')
    setLoading(true)
    try {
      if (stream) {
        // Streaming path with fallback
        try {
          const res = await fetch('/api/chat?stream=1', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ model: selected, messages: newMsgs, context: { memory: memSelected, files: fsSelected, git: { diffs: gitSelected } }, stream: true }) })
          if (!res.ok || !res.body) throw new Error(`stream http ${res.status}`)
          const reader = res.body.getReader()
          const decoder = new TextDecoder()
          let assistant = ''
          // Append placeholder assistant message with optional role tag
          setMessages(prev => [...prev, { role: 'assistant', content: '', metaAgentRole: activeAgentRole || undefined }])
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            const chunk = decoder.decode(value)
            // Parse SSE: lines start with "data: "
            const lines = chunk.split(/\r?\n/)
            for (const line of lines) {
              const trimmed = line.trim()
              if (!trimmed.startsWith('data:')) continue
              const data = trimmed.slice(5).trim()
              if (data === '[DONE]') continue
              try {
                const obj = JSON.parse(data)
                const delta = obj?.choices?.[0]?.delta?.content || ''
                if (delta) {
                  assistant += delta
                  // Update last assistant message incrementally
                  setMessages(prev => {
                    const copy = [...prev]
                    copy[copy.length - 1] = { role: 'assistant', content: assistant, metaAgentRole: activeAgentRole || undefined }
                    return copy
                  })
                }
              } catch {
                // ignore JSON parse errors
              }
            }
          }
        } catch (e) {
          // Fallback to non-stream
          const r = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ model: selected, messages: newMsgs, context: { memory: memSelected, files: fsSelected, git: { diffs: gitSelected } } }) })
          const d = await r.json()
          if (d?.message) setMessages((prev) => [...prev, { ...d.message, metaAgentRole: activeAgentRole || undefined }])
          else setMessages((prev) => [...prev, { role: 'assistant', content: d?.error ? `Error: ${d.error}` : 'No response' }])
        }
      } else {
        const r = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ model: selected, messages: newMsgs, context: { memory: memSelected, files: fsSelected, git: { diffs: gitSelected } } }) })
        const d = await r.json()
        if (d?.message) setMessages((prev) => [...prev, { ...d.message, metaAgentRole: activeAgentRole || undefined }])
        else setMessages((prev) => [...prev, { role: 'assistant', content: d?.error ? `Error: ${d.error}` : 'No response' }])
      }
    } catch (e:any) {
      setMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${e?.message ?? 'unknown'}` }])
    } finally {
      setLoading(false)
    }
  }

  const loadMemory = async () => {
    try {
      const r = await fetch(`/api/context/memory?q=${encodeURIComponent(memQuery)}`, { cache: 'no-store' })
      const d = await r.json()
      setMemItems(Array.isArray(d.items) ? d.items : [])
    } catch { setMemItems([]) }
  }
  const loadFS = async () => {
    try {
      const r = await fetch(`/api/context/fs?pattern=${encodeURIComponent(fsPattern)}`, { cache: 'no-store' })
      const d = await r.json()
      setFsFiles(Array.isArray(d.files) ? d.files : [])
    } catch { setFsFiles([]) }
  }
  const previewFS = async () => {
    if (!fsSnippetPath) return
    setFsPreview('')
    setFsPreviewLoading(true)
    try {
      const body:any = { path: fsSnippetPath }
      const s = parseInt(fsStart, 10); const e = parseInt(fsEnd, 10)
      if (!isNaN(s)) body.start = s
      if (!isNaN(e)) body.end = e
      const r = await fetch('/api/context/fs', { method: 'POST', headers: { 'Content-Type':'application/json' }, body: JSON.stringify(body) })
      const d = await r.json()
      if (d?.ok) setFsPreview(d.content || '')
      else setFsPreview(`Error: ${d?.error || 'fs-read-failed'}`)
    } catch (e:any) {
      setFsPreview(`Error: ${e?.message || 'failed'}`)
    } finally {
      setFsPreviewLoading(false)
    }
  }
  const attachFSSnippet = () => {
    if (!fsSnippetPath) return
    const s = parseInt(fsStart, 10); const e = parseInt(fsEnd, 10)
    setFsSelected((prev)=>[...prev, { path: fsSnippetPath, start: isNaN(s)? undefined : s, end: isNaN(e)? undefined : e }])
  }
  const loadGit = async () => {
    try {
      const r = await fetch(`/api/context/git?mode=symbols&query=${encodeURIComponent(gitQuery)}`, { cache: 'no-store' })
      const d = await r.json()
      setGitResults(Array.isArray(d.results) ? d.results : [])
    } catch { setGitResults([]) }
  }

  const allAliasOptions = useMemo(() => Object.keys(aliases || {}), [aliases])
  const allModelOptions = useMemo(() => models.map(m => m.id), [models])
  const aliasOrModelOptions = useMemo(() => {
    const set = new Set<string>([...allAliasOptions, ...allModelOptions])
    return Array.from(set).sort()
  }, [allAliasOptions, allModelOptions])

  const onProfileSave = async () => {
    setSavingProfile(true)
    try {
      const r = await fetch('/api/agents/profile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(profile) })
      const d = await r.json()
      if (!d?.ok) alert(`Failed to save profile: ${d?.error || 'unknown'}`)
    } catch (e:any) {
      alert(`Save error: ${e?.message || 'unknown'}`)
    } finally {
      setSavingProfile(false)
    }
  }

  const addAgentRow = () => {
    setProfile((prev) => ({ ...prev, agents: [...prev.agents, { role: 'role', aliasOrModel: aliasOrModelOptions[0] || 'claude', temperature: 0.3, tools: [] }] }))
  }
  const removeAgentRow = (idx: number) => setProfile((prev) => ({ ...prev, agents: prev.agents.filter((_,i)=>i!==idx) }))
  const resolveAliasOrModel = (value: string) => {
    if (aliases && Object.prototype.hasOwnProperty.call(aliases, value)) return aliases[value]
    return value
  }
  const useCoderModel = () => {
    const coder = profile.agents.find(a => a.role.toLowerCase().includes('coder'))
    if (!coder) { alert('No coder row found in profile'); return }
    const model = resolveAliasOrModel(coder.aliasOrModel)
    setSelected(model)
  }
  const useArchitectModel = () => {
    const row = profile.agents.find(a => a.role.toLowerCase().includes('architect'))
    if (!row) { alert('No architect row found in profile'); return }
    const model = resolveAliasOrModel(row.aliasOrModel)
    setSelected(model)
  }
  const useReviewerModel = () => {
    const row = profile.agents.find(a => a.role.toLowerCase().includes('review'))
    if (!row) { alert('No reviewer row found in profile'); return }
    const model = resolveAliasOrModel(row.aliasOrModel)
    setSelected(model)
  }
  const runProfileParallel = async () => {
    const text = input.trim()
    if (!text) { alert('Type a prompt first'); return }
    if (!profile.agents.length) { alert('No agents defined in profile'); return }
    // Append the user message once
    const userMsg: Msg = { role: 'user', content: text }
    const baseMsgs = [...messages, userMsg]
    setMessages(baseMsgs)
    setInput('')
    setLoading(true)
    try {
      const ctx = { memory: memSelected, files: fsSelected, git: { diffs: gitSelected } }
      const tasks = profile.agents.map(async (a) => {
        const model = resolveAliasOrModel(a.aliasOrModel)
        try {
          const r = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ model, messages: baseMsgs, context: ctx, params: { temperature: a.temperature } }) })
          const d = await r.json()
          if (d?.message) setMessages(prev => [...prev, { ...d.message, metaAgentRole: a.role }])
          else setMessages(prev => [...prev, { role: 'assistant', content: d?.error ? `(${a.role}) Error: ${d.error}` : `(${a.role}) No response`, metaAgentRole: a.role }])
        } catch (e:any) {
          setMessages(prev => [...prev, { role: 'assistant', content: `(${a.role}) Error: ${e?.message || 'failed'}`, metaAgentRole: a.role }])
        }
      })
      await Promise.allSettled(tasks)
    } finally {
      setLoading(false)
    }
  }

  const modelOptions = useMemo(() => {
    return models.sort((a,b)=>a.provider.localeCompare(b.provider)).map(m => ({ value: m.id, label: `${m.id} (${m.provider})` }))
  }, [models])

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Sophia Studio</h1>
      <div className="flex items-center gap-3 text-sm">
        <span className={status?.litellm? 'text-green-600':'text-red-600'}>LiteLLM: {status?.litellm? 'OK':'Down'}</span>
        <span className={(status?.mcp?.memory? 'text-green-600':'text-yellow-700')+ ' ml-2'}>MCP Memory</span>
        <span className={(status?.mcp?.fs? 'text-green-600':'text-yellow-700')+ ' ml-2'}>FS</span>
        <span className={(status?.mcp?.git? 'text-green-600':'text-yellow-700')+ ' ml-2'}>Git</span>
        <span className="ml-4 text-slate-700">Reqs: {obs.count ?? 0}</span>
        <span className="text-slate-700">p50: {obs.p50 ?? '-' } ms</span>
        <span className="text-slate-700">p95: {obs.p95 ?? '-' } ms</span>
        <button className="ml-2 px-2 border rounded text-xs" onClick={async()=>{ try{ const r=await fetch('/api/observability',{cache:'no-store'}); const d=await r.json(); if(d?.ok) setObs({ count:d.count, p50:d.p50??null, p95:d.p95??null, models:d.models||{} }) }catch{}}}>Refresh</button>
      </div>
      <div className="flex gap-2 items-center">
        <label className="text-sm">Model</label>
        <select value={selected} onChange={(e)=>setSelected(e.target.value)} className="border rounded px-2 py-1">
          {modelOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
        </select>
        <label className="ml-2 text-sm flex items-center gap-1"><input type="checkbox" checked={stream} onChange={(e)=>setStream(e.target.checked)} /> Stream</label>
        <label className="ml-2 text-sm">Active Agent</label>
        <select value={activeAgentRole} onChange={(e)=>{
          const role = e.target.value
          setActiveAgentRole(role)
          if (role) {
            const m = getModelForRole(role)
            if (m) setSelected(m)
          }
        }} className="border rounded px-2 py-1">
          <option value="">(none)</option>
          {profile.agents.map((a,idx)=>(<option key={`${a.role}-${idx}`} value={a.role}>{a.role}</option>))}
        </select>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 border rounded p-3 space-y-3">
          <div className="space-y-2 max-h-[50vh] overflow-auto">
            {messages.map((m, i)=> (
              <div key={i} className={m.role==='user'? 'text-slate-900':'text-slate-700'}>
                <b>{m.role}</b>
                {m.metaAgentRole && <span className="ml-2 inline-block text-[10px] px-2 py-0.5 rounded bg-slate-200 text-slate-700">{m.metaAgentRole}</span>}
                {': '} {m.content}
              </div>
            ))}
            {messages.length===0 && <div className="text-slate-500">No messages yet. Type below and press Send.</div>}
          </div>
          <div className="flex gap-2">
            <textarea value={input} onChange={(e)=>setInput(e.target.value)} rows={3} className="flex-1 border rounded p-2" placeholder="Ask or instruct..." />
            <div className="flex flex-col gap-2">
              <button onClick={onSend} disabled={loading} className="px-3 py-2 text-white bg-blue-600 rounded disabled:opacity-60">{loading? 'Sending...':'Send'}</button>
              <button onClick={runProfileParallel} disabled={loading || !profile.agents.length} className="px-3 py-2 text-white bg-purple-600 rounded disabled:opacity-60">{loading? 'Running...':'Run Profile (parallel)'}</button>
            </div>
          </div>
          <div className="text-xs text-slate-500">Aliases: {Object.keys(aliases).length>0 ? Object.entries(aliases).map(([k,v])=>`${k}→${v}`).join(', ') : 'loading...'}</div>
          <div className="text-xs text-slate-600 mt-1">
            <div className="font-medium">Selected Context</div>
            <div>Memory: {memSelected.length} item(s){memSelected.slice(0,2).map((m,i)=>` | ${m.slice(0,80)}${m.length>80?'…':''}`)}</div>
            <div>Files: {fsSelected.length} {fsSelected.slice(0,3).map((f)=>` | ${f.path}${f.start?`:${f.start}`:''}${f.end?`-${f.end}`:''}`)}</div>
            <div>Git: {gitSelected.length} item(s)</div>
          </div>
        </div>
        <div className="col-span-1 border rounded p-3 space-y-3">
          <h2 className="font-medium">Context</h2>
          <div className="space-y-2">
            <div className="text-sm font-medium">Memory</div>
            <div className="flex gap-2">
              <input value={memQuery} onChange={(e)=>setMemQuery(e.target.value)} placeholder="search" className="border rounded px-2 py-1 flex-1" />
              <button onClick={loadMemory} className="px-2 border rounded">Load</button>
            </div>
            <div className="max-h-32 overflow-auto border rounded p-2 text-xs space-y-1">
              {memItems.map((it,idx)=> (
                <label key={idx} className="flex items-center gap-2"><input type="checkbox" checked={memSelected.includes(it)} onChange={(e)=>{
                  setMemSelected((prev)=> e.target.checked? [...prev,it] : prev.filter(x=>x!==it))
                }} /> <span className="truncate" title={it}>{it}</span></label>
              ))}
              {memItems.length===0 && <div className="text-slate-500">No results</div>}
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-sm font-medium">Filesystem</div>
            <div className="flex gap-2">
              <input value={fsPattern} onChange={(e)=>setFsPattern(e.target.value)} placeholder="pattern (e.g. *.ts)" className="border rounded px-2 py-1 flex-1" />
              <button onClick={loadFS} className="px-2 border rounded">Load</button>
            </div>
            <div className="max-h-32 overflow-auto border rounded p-2 text-xs space-y-1">
              {fsFiles.map((f)=> (
                <label key={f} className="flex items-center gap-2"><input type="checkbox" checked={!!fsSelected.find(x=>x.path===f && x.start===undefined && x.end===undefined)} onChange={(e)=>{
                  setFsSelected((prev)=> e.target.checked? [...prev,{path:f}] : prev.filter(x=>x.path!==f))
                }} /> <span className="truncate" title={f}>{f}</span>
                <button className="ml-auto px-2 border rounded" onClick={()=>{ setFsSnippetPath(f); setFsPreview('') }}>Snippet</button>
                </label>
              ))}
              {fsFiles.length===0 && <div className="text-slate-500">No files</div>}
            </div>
            {fsSnippetPath && (
              <div className="border rounded p-2 text-xs space-y-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium">Snippet for:</span>
                  <span className="truncate" title={fsSnippetPath}>{fsSnippetPath}</span>
                </div>
                <div className="flex gap-2 items-center">
                  <label>Start</label>
                  <input value={fsStart} onChange={(e)=>setFsStart(e.target.value)} className="border rounded px-2 py-1 w-20" />
                  <label>End</label>
                  <input value={fsEnd} onChange={(e)=>setFsEnd(e.target.value)} className="border rounded px-2 py-1 w-20" />
                  <button className="px-2 border rounded" onClick={previewFS} disabled={fsPreviewLoading}>{fsPreviewLoading? 'Loading...':'Preview'}</button>
                  <button className="px-2 border rounded bg-indigo-600 text-white" onClick={attachFSSnippet}>Attach Snippet</button>
                </div>
                <pre className="max-h-40 overflow-auto bg-slate-50 p-2 rounded whitespace-pre-wrap">{fsPreview || 'No preview loaded.'}</pre>
              </div>
            )}
          </div>
          <div className="space-y-2">
            <div className="text-sm font-medium">Git</div>
            <div className="flex gap-2">
              <input value={gitQuery} onChange={(e)=>setGitQuery(e.target.value)} placeholder="symbol query" className="border rounded px-2 py-1 flex-1" />
              <button onClick={loadGit} className="px-2 border rounded">Load</button>
            </div>
            <div className="max-h-32 overflow-auto border rounded p-2 text-xs space-y-1">
              {gitResults.map((g,idx)=> (
                <label key={idx} className="flex items-center gap-2"><input type="checkbox" checked={gitSelected.includes(g)} onChange={(e)=>{
                  setGitSelected((prev)=> e.target.checked? [...prev,g] : prev.filter(x=>x!==g))
                }} /> <span className="truncate" title={g}>{g}</span></label>
              ))}
              {gitResults.length===0 && <div className="text-slate-500">No results</div>}
            </div>
          </div>
          <div className="space-y-2 pt-3 border-t">
            <h2 className="font-medium">Profiles</h2>
            <div className="flex items-center gap-2">
              <label className="text-sm">Name</label>
              <input value={profile.name} onChange={(e)=>setProfile({...profile, name: e.target.value})} className="border rounded px-2 py-1 flex-1" />
            </div>
            <div className="space-y-2 max-h-40 overflow-auto">
              {profile.agents.map((a, idx)=> (
                <div key={idx} className="border rounded p-2 text-xs space-y-1">
                  <div className="flex gap-2 items-center">
                    <label className="w-14">Role</label>
                    <input value={a.role} onChange={(e)=>{
                      const v=e.target.value; setProfile(p=>{const c=[...p.agents]; c[idx]={...c[idx], role:v}; return {...p, agents:c}})
                    }} className="border rounded px-2 py-1 flex-1" />
                    <button onClick={()=>removeAgentRow(idx)} className="px-2 border rounded">Del</button>
                  </div>
                  <div className="flex gap-2 items-center">
                    <label className="w-14">Model</label>
                    <select value={a.aliasOrModel} onChange={(e)=>{
                      const v=e.target.value; setProfile(p=>{const c=[...p.agents]; c[idx]={...c[idx], aliasOrModel:v}; return {...p, agents:c}})
                    }} className="border rounded px-2 py-1 flex-1">
                      {aliasOrModelOptions.map(opt=> <option key={opt} value={opt}>{opt}</option>)}
                    </select>
                  </div>
                  <div className="flex gap-2 items-center">
                    <label className="w-14">Temp</label>
                    <input type="number" step="0.1" min={0} max={1} value={a.temperature} onChange={(e)=>{
                      const v=parseFloat(e.target.value); setProfile(p=>{const c=[...p.agents]; c[idx]={...c[idx], temperature:isNaN(v)?0.3:v}; return {...p, agents:c}})
                    }} className="border rounded px-2 py-1 w-24" />
                  </div>
                  <div className="flex gap-2 items-center">
                    <label className="w-14">Tools</label>
                    <input value={a.tools.join(', ')} onChange={(e)=>{
                      const v=e.target.value.split(',').map(s=>s.trim()).filter(Boolean); setProfile(p=>{const c=[...p.agents]; c[idx]={...c[idx], tools:v}; return {...p, agents:c}})
                    }} className="border rounded px-2 py-1 flex-1" placeholder="comma-separated" />
                  </div>
                </div>
              ))}
              {profile.agents.length===0 && <div className="text-slate-500 text-xs">No agents defined.</div>}
            </div>
            <div className="flex gap-2">
              <button onClick={addAgentRow} className="px-2 py-1 border rounded">Add Agent</button>
              <button onClick={onProfileSave} disabled={savingProfile} className="px-2 py-1 border rounded bg-emerald-600 text-white disabled:opacity-60">{savingProfile? 'Saving...':'Save Profile'}</button>
              <button onClick={async()=>{
                try{const r=await fetch('/api/agents/profile',{cache:'no-store'});const d=await r.json();if(d?.ok&&d?.profile)setProfile(d.profile);}catch{}
              }} className="px-2 py-1 border rounded">Reload</button>
              <button onClick={useCoderModel} className="px-2 py-1 border rounded bg-blue-600 text-white">Use Coder Model</button>
              <button onClick={useArchitectModel} className="px-2 py-1 border rounded bg-blue-600 text-white">Use Architect Model</button>
              <button onClick={useReviewerModel} className="px-2 py-1 border rounded bg-blue-600 text-white">Use Reviewer Model</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
