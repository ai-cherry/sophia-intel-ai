import React, { useState, useRef } from 'react'
import { speechToText, sendChatMessage } from '../lib/api'

function VoiceButton() {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRecorderRef.current = new MediaRecorder(stream)
      chunksRef.current = []

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' })
        await processAudio(audioBlob)
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorderRef.current.start()
      setIsRecording(true)
    } catch (error) {
      console.error('Error starting recording:', error)
      alert('Could not access microphone. Please check permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setIsProcessing(true)
    }
  }

  const processAudio = async (audioBlob) => {
    try {
      // Convert speech to text
      const transcription = await speechToText(audioBlob)
      console.log('Transcription:', transcription)

      // Send to chat orchestration
      if (transcription.text) {
        const response = await sendChatMessage(transcription.text)
        console.log('Chat response:', response)
        
        // TODO: Optionally convert response back to speech
        // const audioResponse = await textToSpeech(response.result.response)
      }
    } catch (error) {
      console.error('Error processing audio:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleClick = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  return (
    <div className="voice-button-container">
      <button
        className={`voice-button ${isRecording ? 'recording' : ''} ${isProcessing ? 'processing' : ''}`}
        onClick={handleClick}
        disabled={isProcessing}
      >
        {isProcessing ? '🔄' : isRecording ? '🔴' : '🎙️'}
      </button>
      <div className="voice-status">
        {isProcessing && 'Processing...'}
        {isRecording && 'Recording... Click to stop'}
        {!isRecording && !isProcessing && 'Click to record'}
      </div>
    </div>
  )
}

export default VoiceButton
