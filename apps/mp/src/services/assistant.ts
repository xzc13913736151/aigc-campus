import type { AssistantActionExecuteResponse, AssistantActionProposal, AssistantMessage, AssistantReplyResponse, AssistantSession } from '../types/api'
import { request } from '../utils/request'

export function createAssistantSession(payload: {
  page_type: AssistantSession['page_type']
  title?: string
  context_path?: string
  context_target_type?: string
  context_target_id?: string
}) {
  return request<AssistantSession>('assistant/sessions/', {
    method: 'POST',
    data: payload,
  })
}

export function fetchAssistantSessions() {
  return request<AssistantSession[]>('assistant/sessions/')
}

export function fetchAssistantMessages(sessionId: string) {
  return request<AssistantMessage[]>(`assistant/sessions/${sessionId}/messages/`)
}

export function fetchAssistantActions(sessionId: string) {
  return request<AssistantActionProposal[]>(`assistant/sessions/${sessionId}/actions/`)
}

export function sendAssistantMessage(sessionId: string, payload: { body: string }) {
  return request<AssistantReplyResponse>(`assistant/sessions/${sessionId}/messages/`, {
    method: 'POST',
    data: payload,
    timeout: 70000,
  })
}

export function executeAssistantAction(actionId: string) {
  return request<AssistantActionExecuteResponse>(`assistant/actions/${actionId}/execute/`, {
    method: 'POST',
  })
}
