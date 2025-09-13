"use client"
import React, { useEffect, useState } from 'react'

type ProviderInfo = { vk?: string; present: boolean }

export default function ProvidersPage() {
  const [data, setData] = useState<{ portkey: boolean; providers: Record<string, ProviderInfo> }|null>(null)
  useEffect(()=>{ void (async ()=>{
    try { const r = await fetch('/api/providers/vk', { cache: 'no-store' }); const d = await r.json(); setData(d) } catch {}
  })() },[])
  const providers = data?.providers || {}
  return (
    <div className="max-w-3xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Provider Virtual Keys</h1>
      <div className="text-sm">Portkey configured: <b>{data?.portkey ? 'Yes' : 'No'}</b></div>
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="text-left border-b">
            <th className="py-2">Provider</th>
            <th className="py-2">VK Present</th>
            <th className="py-2">Value</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(providers).map(([prov, info]) => (
            <tr key={prov} className="border-b">
              <td className="py-2 capitalize">{prov.replace('_',' ')}</td>
              <td className="py-2">{info.present? '✅' : '—'}</td>
              <td className="py-2 font-mono text-xs truncate" title={info.vk || ''}>{info.vk || ''}</td>
            </tr>
          ))}
          {Object.keys(providers).length===0 && (
            <tr><td colSpan={3} className="py-4 text-slate-500">No provider VKs detected</td></tr>
          )}
        </tbody>
      </table>
      <div className="text-xs text-slate-600">
        Tip: Add VKs in .env.master like PORTKEY_VK_OPENROUTER, PORTKEY_VK_TOGETHER, PORTKEY_VK_HUGGINGFACE.
      </div>
    </div>
  )
}

