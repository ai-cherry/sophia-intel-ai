export const APIRoutes = {
  GetConfig: (PlaygroundApiUrl: string) =>
    `${PlaygroundApiUrl}/config`,
  GetPlaygroundAgents: (PlaygroundApiUrl: string) =>
    `${PlaygroundApiUrl}/agents`,
  AgentRun: (PlaygroundApiUrl: string) =>
    `${PlaygroundApiUrl}/agents/{agent_id}/runs`,
  PlaygroundStatus: (PlaygroundApiUrl: string) =>
    `${PlaygroundApiUrl}/healthz`,
  GetPlaygroundSessions: (PlaygroundApiUrl: string, agentId: string) =>
    `${PlaygroundApiUrl}/agents/${agentId}/sessions`,
  GetPlaygroundSession: (
    PlaygroundApiUrl: string,
    agentId: string,
    sessionId: string
  ) =>
    `${PlaygroundApiUrl}/agents/${agentId}/sessions/${sessionId}`,

  DeletePlaygroundSession: (
    PlaygroundApiUrl: string,
    agentId: string,
    sessionId: string
  ) =>
    `${PlaygroundApiUrl}/agents/${agentId}/sessions/${sessionId}`,

  GetPlayGroundTeams: (PlaygroundApiUrl: string) =>
    `${PlaygroundApiUrl}/teams`,
  TeamRun: (PlaygroundApiUrl: string, teamId: string) =>
    `${PlaygroundApiUrl}/teams/run`,
  GetPlaygroundTeamSessions: (PlaygroundApiUrl: string, teamId: string) =>
    `${PlaygroundApiUrl}/teams/${teamId}/sessions`,
  GetPlaygroundTeamSession: (
    PlaygroundApiUrl: string,
    teamId: string,
    sessionId: string
  ) =>
    `${PlaygroundApiUrl}/teams/${teamId}/sessions/${sessionId}`,
  DeletePlaygroundTeamSession: (
    PlaygroundApiUrl: string,
    teamId: string,
    sessionId: string
  ) => `${PlaygroundApiUrl}/teams/${teamId}/sessions/${sessionId}`,
  
  // Cost tracking routes
  GetCostSummary: (PlaygroundApiUrl: string) =>
    `${PlaygroundApiUrl}/costs/summary`,
  GetDailyCosts: (PlaygroundApiUrl: string) =>
    `${PlaygroundApiUrl}/costs/daily`,
  GetTopModels: (PlaygroundApiUrl: string) =>
    `${PlaygroundApiUrl}/costs/models`,
  RecordCostEvent: (PlaygroundApiUrl: string) =>
    `${PlaygroundApiUrl}/costs/record`
}
