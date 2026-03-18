export interface ChatMessage {
  role: 'user' | 'agent' | 'tool';
  content: string;
}

export interface ChatResponse {
  response: string;
  map_url: string | null;
  messages: ChatMessage[];
}

const API_BASE_URL = 'http://127.0.0.1:8000';

export async function sendMessage(message: string, sessionId: string = 'default'): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, session_id: sessionId })
  });
  
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  
  return res.json();
}
