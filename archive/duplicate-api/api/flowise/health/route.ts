import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(request: NextRequest) {
  try {
    // Try to get Flowise factories status as health check
    const response = await fetch(`${BACKEND_URL}/api/flowwise/factories`, {
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.ok) {
      const data = await response.json()
      // Handle both array response and object with factories property
      const factoryCount = Array.isArray(data)
        ? data.length
        : (data.factories?.length || 0)

      return NextResponse.json({
        status: factoryCount > 0 ? 'healthy' : 'ready',
        factories: factoryCount,
        timestamp: new Date().toISOString()
      })
    }

    return NextResponse.json({
      status: 'degraded',
      message: 'Backend responding but no factories found',
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    console.error('Flowise health check error:', error)

    return NextResponse.json({
      status: 'offline',
      message: 'Unable to connect to Flowise backend',
      timestamp: new Date().toISOString()
    })
  }
}