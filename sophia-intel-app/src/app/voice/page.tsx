import dynamic from 'next/dynamic'

export const metadata = {
  title: 'Voice Coding · Sophia Intel',
  description: 'Mobile-optimized voice interface for Sophia Intel'
}

const MobileVoiceInterface = dynamic(() => import('@/components/voice/MobileVoiceInterface'), { ssr: false })

export default function VoicePage() {
  return (
    <main className="py-8">
      <div className="max-w-md mx-auto px-4">
        <h1 className="text-2xl font-semibold mb-2">Voice Coding</h1>
        <p className="opacity-80 mb-6 text-sm">
          Hold the button and speak your request. Generated code and responses will appear below.
        </p>
        <MobileVoiceInterface />
      </div>
    </main>
  )
}

