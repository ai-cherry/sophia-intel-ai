import { toast } from 'sonner'

import { APIRoutes } from './routes'
import { ApiClient } from '@/lib/api/client'
import { useUnifiedStore } from '@/lib/state/unifiedStore'

import {
  Agent,
  ComboboxAgent,
  SessionEntry,
  ComboboxTeam,
  Team
} from '@/types/playground'

export const getPlaygroundAgentsAPI = async (
  endpoint: string
): Promise<ComboboxAgent[]> => {
  const url = APIRoutes.GetPlaygroundAgents(endpoint)
  try {
    const client = new ApiClient('', (cat, ms) => useUnifiedStore.getState().updateLatency(cat, ms))
    const data = await client.get<any[]>(url, { category: 'api.playground.agents' })
    // Transform the API response into the expected shape.
    // Transform and filter to ensure non-empty values
    const agents: ComboboxAgent[] = data
      .map((item: Agent) => ({
        value: item.agent_id || item.id || item.name || '',
        label: item.name || item.id || item.agent_id || 'Unknown',
        model: {
          provider: item.model?.provider || item.model_pool || 'unknown'
        },
        storage: !!item.storage
      }))
      .filter((agent) => agent.value !== '')
    return agents
  } catch {
    toast.error('Error fetching playground agents')
    return []
  }
}

export const getPlaygroundStatusAPI = async (base: string): Promise<number> => {
  const client = new ApiClient(base, (cat, ms) => useUnifiedStore.getState().updateLatency(cat, ms))
  const res = await fetch(APIRoutes.PlaygroundStatus(base), { method: 'GET' })
  // Keep legacy behavior for now but record timing via a no-op GET
  client.get('/noop', { category: 'api.playground.status' }).catch(() => {})
  return res.status
}

export const getAllPlaygroundSessionsAPI = async (
  base: string,
  agentId: string
): Promise<SessionEntry[]> => {
  try {
    const client = new ApiClient('', (cat, ms) => useUnifiedStore.getState().updateLatency(cat, ms))
    const url = APIRoutes.GetPlaygroundSessions(base, agentId)
    const response = await fetch(url, { method: 'GET' })
    if (!response.ok) {
      if (response.status === 404) {
        return []
      }
      throw new Error(`Failed to fetch sessions: ${response.statusText}`)
    }
    const data = await response.json()
    // Emit timing sample via client to keep category grouping consistent
    client.get('/noop', { category: 'api.playground.sessions' }).catch(() => {})
    return data
  } catch {
    return []
  }
}

export const getPlaygroundSessionAPI = async (
  base: string,
  agentId: string,
  sessionId: string
) => {
  const client = new ApiClient('', (cat, ms) => useUnifiedStore.getState().updateLatency(cat, ms))
  const response = await fetch(APIRoutes.GetPlaygroundSession(base, agentId, sessionId), { method: 'GET' })
  return response.json()
}

export const deletePlaygroundSessionAPI = async (
  base: string,
  agentId: string,
  sessionId: string
) => {
  const client = new ApiClient('', (cat, ms) => useUnifiedStore.getState().updateLatency(cat, ms))
  const response = await fetch(APIRoutes.DeletePlaygroundSession(base, agentId, sessionId), { method: 'DELETE' })
  client.get('/noop', { category: 'api.playground.deleteSession' }).catch(() => {})
  return response
}

export const getPlaygroundTeamsAPI = async (
  endpoint: string
): Promise<ComboboxTeam[]> => {
  const url = APIRoutes.GetPlayGroundTeams(endpoint)
  try {
    const client = new ApiClient('', (cat, ms) => useUnifiedStore.getState().updateLatency(cat, ms))
    const data = await client.get<any[]>(url, { category: 'api.playground.teams' })
    // Transform the API response into the expected shape.
    // Transform and filter to ensure non-empty values
    const teams: ComboboxTeam[] = data
      .map((item: Team) => ({
        value: item.team_id || item.id || item.name || '',
        label: item.name || item.id || item.team_id || 'Unknown',
        model: {
          provider: item.model?.provider || item.model_pool || 'unknown'
        },
        storage: !!item.storage
      }))
      .filter((team) => team.value !== '')
    return teams
  } catch {
    toast.error('Error fetching playground teams')
    return []
  }
}

export const getPlaygroundTeamSessionsAPI = async (
  base: string,
  teamId: string
): Promise<SessionEntry[]> => {
  try {
    const response = await fetch(
      APIRoutes.GetPlaygroundTeamSessions(base, teamId),
      {
        method: 'GET'
      }
    )
    if (!response.ok) {
      if (response.status === 404) {
        return []
      }
      throw new Error(`Failed to fetch team sessions: ${response.statusText}`)
    }
    return response.json()
  } catch (error) {
    console.error('Error fetching team sessions:', error)
    toast.error('Error fetching team sessions') // Inform user
    return []
  }
}

export const getPlaygroundTeamSessionAPI = async (
  base: string,
  teamId: string,
  sessionId: string
) => {
  const response = await fetch(
    APIRoutes.GetPlaygroundTeamSession(base, teamId, sessionId),
    {
      method: 'GET'
    }
  )
  if (!response.ok) {
    throw new Error(`Failed to fetch team session: ${response.statusText}`)
  }
  return response.json()
}

export const deletePlaygroundTeamSessionAPI = async (
  base: string,
  teamId: string,
  sessionId: string
) => {
  const response = await fetch(
    APIRoutes.DeletePlaygroundTeamSession(base, teamId, sessionId),
    {
      method: 'DELETE'
    }
  )

  if (!response.ok) {
    throw new Error(`Failed to delete team session: ${response.statusText}`)
  }
  return response
}