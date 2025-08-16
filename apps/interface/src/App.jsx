import React, { useState } from 'react'
import Chat from './components/Chat'
import VoiceButton from './components/VoiceButton'
import Missions from './components/Missions'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('chat')

  return (
    <div className="app">
      <header className="app-header">
        <h1>🧠 SOPHIA Intel</h1>
        <p>AI Command Center</p>
      </header>

      <nav className="app-nav">
        <button 
          className={activeTab === 'chat' ? 'active' : ''}
          onClick={() => setActiveTab('chat')}
        >
          💬 Chat
        </button>
        <button 
          className={activeTab === 'missions' ? 'active' : ''}
          onClick={() => setActiveTab('missions')}
        >
          🎯 Missions
        </button>
      </nav>

      <main className="app-main">
        {activeTab === 'chat' && (
          <div className="chat-container">
            <Chat />
            <VoiceButton />
          </div>
        )}
        {activeTab === 'missions' && <Missions />}
      </main>
    </div>
  )
}

export default App
