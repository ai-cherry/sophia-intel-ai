import React, { useState } from 'react'
import { sendCodeRequest } from '../lib/api'

function Missions() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const handleCreateBranch = async () => {
    setLoading(true)
    setResult(null)

    try {
      const response = await sendCodeRequest({
        operation: 'create_branch',
        branch_name: 'feature/sophia-enhancement',
        description: 'SOPHIA-generated enhancement branch'
      })
      setResult(response)
    } catch (error) {
      console.error('Mission failed:', error)
      setResult({ error: error.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="missions">
      <h2>🎯 Mission Control</h2>
      <p>Execute code operations and GitHub missions</p>

      <div className="mission-card">
        <h3>Create Feature Branch</h3>
        <p>Create a new feature branch for development</p>
        <button 
          onClick={handleCreateBranch}
          disabled={loading}
          className="mission-button"
        >
          {loading ? 'Creating...' : 'Create Branch'}
        </button>
      </div>

      {result && (
        <div className="mission-result">
          <h4>Mission Result:</h4>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

export default Missions
