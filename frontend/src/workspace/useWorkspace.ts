import { useContext } from 'react'
import { WorkspaceContext } from './WorkspaceContext'

export function useWorkspace() {
  const ctx = useContext(WorkspaceContext)
  if (!ctx) throw new Error('useWorkspace requires WorkspaceProvider')
  return ctx
}
