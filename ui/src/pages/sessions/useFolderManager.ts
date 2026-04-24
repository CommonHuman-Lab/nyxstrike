import { useCallback, useState } from 'react'
import { api } from '../../api'
import { useToast } from '../../components/ToastProvider'

function slugify(raw: string): string {
  return raw
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^a-zA-Z0-9_\-]/g, '')
    .slice(0, 120)
}

interface DeleteFolderTarget {
  folder: string
  noteCount: number
}

export interface UseFolderManagerReturn {
  // Create
  showNewFolderInput: boolean
  newFolderName: string
  newFolderError: string | null
  creatingFolder: boolean
  setShowNewFolderInput: React.Dispatch<React.SetStateAction<boolean>>
  setNewFolderName: React.Dispatch<React.SetStateAction<string>>
  createFolder: (name: string) => Promise<void>

  // Rename
  renamingFolder: string | null
  renameDraft: string
  renameError: string | null
  renameSaving: boolean
  startRenameFolder: (folder: string) => void
  cancelRenameFolder: () => void
  confirmRenameFolder: () => Promise<void>
  setRenameDraft: React.Dispatch<React.SetStateAction<string>>

  // Delete
  deleteFolderTarget: DeleteFolderTarget | null
  deletingFolder: boolean
  setDeleteFolderTarget: React.Dispatch<React.SetStateAction<DeleteFolderTarget | null>>
  confirmDeleteFolder: () => Promise<void>

  // Expanded state
  expandedFolders: Set<string>
  toggleFolder: (folder: string) => void
  setExpandedFolders: React.Dispatch<React.SetStateAction<Set<string>>>
}

export function useFolderManager(
  sessionId: string,
  allFolders: string[],
  reloadNotes: () => Promise<void>
): UseFolderManagerReturn {
  const { pushToast } = useToast()

  // Expanded accordion state
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  function toggleFolder(folder: string) {
    setExpandedFolders(prev => {
      const next = new Set(prev)
      if (next.has(folder)) {
        next.delete(folder)
      } else {
        next.add(folder)
      }
      return next
    })
  }

  // Create folder
  const [showNewFolderInput, setShowNewFolderInput] = useState(false)
  const [newFolderName, setNewFolderName] = useState('')
  const [newFolderError, setNewFolderError] = useState<string | null>(null)
  const [creatingFolder, setCreatingFolder] = useState(false)

  const createFolder = useCallback(async (name: string) => {
    const slug = slugify(name)
    if (!slug) { setNewFolderError('Folder name is empty or contains only invalid characters'); return }
    setCreatingFolder(true)
    setNewFolderError(null)
    try {
      await api.createSessionNoteFolder(sessionId, slug)
      pushToast('success', `Folder "${slug}" created`)
      setShowNewFolderInput(false)
      setNewFolderName('')
      await reloadNotes()
      setExpandedFolders(prev => new Set([...prev, slug]))
    } catch (e: unknown) {
      const msg = (e instanceof Error) ? e.message : String(e)
      if (msg.includes('409') || msg.toLowerCase().includes('already exists')) {
        setNewFolderError(`Folder "${slug}" already exists`)
      } else {
        setNewFolderError('Failed to create folder')
      }
    } finally {
      setCreatingFolder(false)
    }
  }, [sessionId, reloadNotes, pushToast])

  // Rename folder
  const [renamingFolder, setRenamingFolder] = useState<string | null>(null)
  const [renameDraft, setRenameDraft] = useState('')
  const [renameError, setRenameError] = useState<string | null>(null)
  const [renameSaving, setRenameSaving] = useState(false)

  function startRenameFolder(folder: string) {
    setRenamingFolder(folder)
    setRenameDraft(folder)
    setRenameError(null)
  }

  function cancelRenameFolder() {
    setRenamingFolder(null)
    setRenameDraft('')
    setRenameError(null)
  }

  const confirmRenameFolder = useCallback(async () => {
    if (!renamingFolder) return
    const slug = slugify(renameDraft)
    if (!slug) { setRenameError('Name is empty or contains only invalid characters'); return }
    if (slug === renamingFolder) { cancelRenameFolder(); return }
    if (allFolders.includes(slug)) { setRenameError(`Folder "${slug}" already exists`); return }
    setRenameSaving(true)
    setRenameError(null)
    try {
      await api.renameSessionNoteFolder(sessionId, renamingFolder, slug)
      pushToast('success', `Folder renamed to "${slug}"`)
      setExpandedFolders(prev => {
        const next = new Set(prev)
        if (next.has(renamingFolder)) {
          next.delete(renamingFolder)
          next.add(slug)
        }
        return next
      })
      cancelRenameFolder()
      await reloadNotes()
    } catch (e: unknown) {
      const msg = (e instanceof Error) ? e.message : String(e)
      if (msg.includes('409') || msg.toLowerCase().includes('already exists')) {
        setRenameError(`Folder "${slug}" already exists`)
      } else {
        setRenameError('Failed to rename folder')
      }
    } finally {
      setRenameSaving(false)
    }
  }, [renamingFolder, renameDraft, allFolders, sessionId, reloadNotes, pushToast])

  // Delete folder
  const [deleteFolderTarget, setDeleteFolderTarget] = useState<DeleteFolderTarget | null>(null)
  const [deletingFolder, setDeletingFolder] = useState(false)

  const confirmDeleteFolder = useCallback(async () => {
    if (!deleteFolderTarget) return
    setDeletingFolder(true)
    try {
      await api.deleteSessionNoteFolder(sessionId, deleteFolderTarget.folder)
      pushToast('success', `Folder "${deleteFolderTarget.folder}" deleted`)
      setExpandedFolders(prev => {
        const next = new Set(prev)
        next.delete(deleteFolderTarget.folder)
        return next
      })
      setDeleteFolderTarget(null)
      await reloadNotes()
    } catch {
      pushToast('error', `Failed to delete folder "${deleteFolderTarget.folder}"`)
    } finally {
      setDeletingFolder(false)
    }
  }, [deleteFolderTarget, sessionId, reloadNotes, pushToast])

  return {
    // Create
    showNewFolderInput,
    newFolderName,
    newFolderError,
    creatingFolder,
    setShowNewFolderInput,
    setNewFolderName,
    createFolder,

    // Rename
    renamingFolder,
    renameDraft,
    renameError,
    renameSaving,
    startRenameFolder,
    cancelRenameFolder,
    confirmRenameFolder,
    setRenameDraft,

    // Delete
    deleteFolderTarget,
    deletingFolder,
    setDeleteFolderTarget,
    confirmDeleteFolder,

    // Expanded
    expandedFolders,
    toggleFolder,
    setExpandedFolders,
  }
}
