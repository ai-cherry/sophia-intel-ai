import { NextApiRequest, NextApiResponse } from 'next'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  try {
    const response = await fetch(`${BACKEND_URL}/api/bi/metrics`, {
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Upstream responded with ${response.status}`)
    }

    const data = await response.json()
    return res.status(200).json(data)
  } catch (error) {
    console.warn('[api/bi/metrics] Falling back to sample data:', error)

    // Return sample metrics as fallback matching backend structure
    return res.status(200).json({
      metrics: {
        revenue: { value: 2450000, change: 12.5, trend: 'up' },
        customers: { value: 8421, change: 8.3, trend: 'up' },
        conversion_rate: { value: 3.2, change: -0.5, trend: 'down' },
        avg_deal_size: { value: 45000, change: 15.2, trend: 'up' }
      },
      timestamp: new Date().toISOString()
    })
  }
}
