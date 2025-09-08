/**
 * Audio utility functions for handling voice/audio in the chat interface
 */

export function decodeBase64Audio(base64: string): Blob {
  // Remove data URL prefix if present
  const base64Data = base64.replace(/^data:audio\/\w+;base64,/, '');
  
  // Convert base64 to binary
  const binaryString = atob(base64Data);
  const bytes = new Uint8Array(binaryString.length);
  
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  
  // Create blob with audio MIME type
  return new Blob([bytes], { type: 'audio/webm' });
}

export function encodeAudioToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      if (reader.result && typeof reader.result === 'string') {
        // Remove data URL prefix to get just base64
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      } else {
        reject(new Error('Failed to encode audio'));
      }
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

export function createAudioURL(blob: Blob): string {
  return URL.createObjectURL(blob);
}

export function revokeAudioURL(url: string): void {
  URL.revokeObjectURL(url);
}

export async function playAudio(audioBlob: Blob): Promise<void> {
  const audioUrl = createAudioURL(audioBlob);
  const audio = new Audio(audioUrl);
  
  return new Promise((resolve, reject) => {
    audio.onended = () => {
      revokeAudioURL(audioUrl);
      resolve();
    };
    audio.onerror = (error) => {
      revokeAudioURL(audioUrl);
      reject(error);
    };
    audio.play().catch(reject);
  });
}

export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];
  
  async startRecording(): Promise<void> {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus'
    });
    
    this.chunks = [];
    
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        this.chunks.push(event.data);
      }
    };
    
    this.mediaRecorder.start();
  }
  
  async stopRecording(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder) {
        reject(new Error('No recording in progress'));
        return;
      }
      
      this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.chunks, { type: 'audio/webm' });
        this.chunks = [];
        
        // Stop all tracks to release microphone
        this.mediaRecorder?.stream.getTracks().forEach(track => track.stop());
        this.mediaRecorder = null;
        
        resolve(blob);
      };
      
      this.mediaRecorder.stop();
    });
  }
  
  isRecording(): boolean {
    return this.mediaRecorder?.state === 'recording';
  }
}