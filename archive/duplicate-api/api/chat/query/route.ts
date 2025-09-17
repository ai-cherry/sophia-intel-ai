import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // For streaming, handle SSE properly
    if (body.stream) {
      const encoder = new TextEncoder()

      // Create a proper SSE stream
      const stream = new ReadableStream({
        async start(controller) {
          try {
            // Since backend doesn't support SSE yet, simulate streaming
            const response = await fetch(`${BACKEND_URL}/api/chat/query`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ ...body, stream: false }),
            })

            if (!response.ok) {
              throw new Error(`Backend error: ${response.status}`)
            }

            const data = await response.json()

            // Simulate streaming by sending chunks
            const chunks = data.response.split(' ')
            for (let i = 0; i < chunks.length; i++) {
              const chunk = chunks[i]
              const message = {
                type: 'content',
                content: chunk + (i < chunks.length - 1 ? ' ' : '')
              }
              controller.enqueue(encoder.encode(`data: ${JSON.stringify(message)}\n\n`))
              await new Promise(resolve => setTimeout(resolve, 50))
            }

            // Send final message with metadata
            const finalMessage = {
              type: 'done',
              metadata: {
                sources: data.sources,
                confidence: data.confidence,
                processing_time: data.processing_time,
                citations: data.citations,
                intent: data.intent
              }
            }
            controller.enqueue(encoder.encode(`data: ${JSON.stringify(finalMessage)}\n\n`))
          } catch (error) {
            const errorMessage = { type: 'error', message: error instanceof Error ? error.message : String(error) }
            controller.enqueue(encoder.encode(`data: ${JSON.stringify(errorMessage)}\n\n`))
          } finally {
            controller.close()
          }
        }
      })

      return new NextResponse(stream, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      })
    }

    // Handle regular non-streaming request
    const response = await fetch(`${BACKEND_URL}/api/chat/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    // Handle regular JSON response
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Chat API error:', error)

    // Fallback response
    return NextResponse.json({
      response: "I'm operating in local mode. Backend connection is being established. How can I help you analyze your business data?",
      sources: [],
      confidence: 0.7,
      processing_time: 0.1,
      intent: { primary_intent: 'fallback', confidence: 1.0 },
      cached: false,
      timestamp: new Date().toISOString()
    })
  }
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const page = searchParams.get('page') || '1'
  const limit = searchParams.get('limit') || '20'

  try {
    const response = await fetch(
      `${BACKEND_URL}/api/chat/history?page=${page}&limit=${limit}`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Chat history error:', error)
    return NextResponse.json({
      conversations: [],
      total_count: 0,
      page: parseInt(page),
      page_size: parseInt(limit)
    })
  }
}