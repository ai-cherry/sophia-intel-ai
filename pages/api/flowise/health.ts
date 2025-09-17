import { NextApiRequest, NextApiResponse } from 'next'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  try {
    const response = await fetch(`${BACKEND_URL}/api/flowwise/factories`, {
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Upstream responded with ${response.status}`)
    }

    const data = await response.json()
    const factoryCount = Array.isArray(data)
      ? data.length
      : (data.factories?.length || 0)

    return res.status(200).json({
      status: factoryCount > 0 ? 'healthy' : 'ready',
      factories: factoryCount,
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    console.warn('[api/flowise/health] Falling back to offline status:', error)

    return res.status(200).json({
      status: 'offline',
      factories: 0,
      message: 'Unable to connect to Flowise backend',
      timestamp: new Date().toISOString()
    })
  }
}
