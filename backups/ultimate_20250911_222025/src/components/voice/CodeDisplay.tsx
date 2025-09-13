"use client"

type Props = {
  code: string
  onCopy?: () => void
}

export default function CodeDisplay({ code, onCopy }: Props) {
  return (
    <div className="bg-white/10 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-semibold">Generated Code</h4>
        <button
          className="text-sm px-2 py-1 rounded bg-white/20 border border-white/30"
          onClick={() => {
            navigator.clipboard.writeText(code).catch(() => {})
            onCopy?.()
          }}
        >
          Copy
        </button>
      </div>
      <pre className="overflow-x-auto text-sm">
        <code>{code}</code>
      </pre>
    </div>
  )
}

