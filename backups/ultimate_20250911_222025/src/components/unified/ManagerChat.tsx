'use client';

import React from 'react';

interface ManagerChatProps {
  teamId?: string | null;
  onTeamSelect?: (teamId: string) => void;
}

export function ManagerChat({ teamId, onTeamSelect }: ManagerChatProps) {
  return (
    <div className="bg-white/5 rounded-lg border border-white/10 p-4">
      <h3 className="text-lg font-semibold mb-3">Manager Chat</h3>
      <div className="text-sm text-white/70">
        {teamId ? `Managing team: ${teamId}` : 'No team selected'}
      </div>
      <div className="mt-4 p-3 bg-white/5 rounded text-sm">
        Manager chat interface will be implemented here
      </div>
    </div>
  );
}