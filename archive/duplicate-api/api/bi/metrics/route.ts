import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/bi/metrics`, {
      headers: {
        'Content-Type': 'application/json',
      },
    })

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('BI Metrics API error:', error)

    // Return sample metrics as fallback
    return NextResponse.json({
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