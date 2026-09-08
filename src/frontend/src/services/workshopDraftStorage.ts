import type { ApiDeliveryStatus } from '../types/registrationApi'
import type { WorkshopProcess } from '../types/workshopProcess'

const DRAFT_STORAGE_KEY = 'cartech.active-workshop-draft.v1'

type StoredWorkshopDraft = {
  version: 1
  process: WorkshopProcess
  failedDelivery?: ApiDeliveryStatus
}

/**
 * Keep the active mechanic draft recoverable after a browser refresh.
 *
 * Session storage deliberately scopes the data to the current browser tab. It
 * is long-lived enough for a retry after an interruption, without leaving a
 * registration on a shared workshop device indefinitely.
 */
export function loadWorkshopDraft(): StoredWorkshopDraft | null {
  const storage = getSessionStorage()
  if (!storage) {
    return null
  }

  try {
    const storedValue = storage.getItem(DRAFT_STORAGE_KEY)
    if (!storedValue) {
      return null
    }

    const parsedValue: unknown = JSON.parse(storedValue)
    return isStoredWorkshopDraft(parsedValue) ? parsedValue : null
  } catch {
    // A malformed or unavailable browser storage must never block the
    // mechanic from continuing the current form.
    return null
  }
}

export function saveWorkshopDraft(
  process: WorkshopProcess,
  failedDelivery?: ApiDeliveryStatus,
) {
  const storage = getSessionStorage()
  if (!storage) {
    return
  }

  const draft: StoredWorkshopDraft = {
    version: 1,
    process,
    ...(failedDelivery ? { failedDelivery } : {}),
  }

  try {
    storage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(draft))
  } catch {
    // Storage can be unavailable or full (for example in private browsing).
    // The live React state remains the source for this session either way.
  }
}

export function clearWorkshopDraft() {
  const storage = getSessionStorage()
  if (!storage) {
    return
  }

  try {
    storage.removeItem(DRAFT_STORAGE_KEY)
  } catch {
    // Ignore browser storage failures; they do not affect the in-memory draft.
  }
}

function getSessionStorage(): Storage | null {
  try {
    return window.sessionStorage
  } catch {
    return null
  }
}

function isStoredWorkshopDraft(value: unknown): value is StoredWorkshopDraft {
  if (!isObject(value) || value.version !== 1 || !isWorkshopProcess(value.process)) {
    return false
  }

  return value.failedDelivery === undefined || isDeliveryStatus(value.failedDelivery)
}

function isWorkshopProcess(value: unknown): value is WorkshopProcess {
  return (
    isObject(value) &&
    typeof value.id === 'string' &&
    (value.serviceType === 'tire_change' || value.serviceType === 'tire_storage') &&
    value.status === 'draft' &&
    typeof value.licensePlate === 'string' &&
    Array.isArray(value.tireSets) &&
    Array.isArray(value.tireInspections) &&
    Array.isArray(value.conditions)
  )
}

function isDeliveryStatus(value: unknown): value is ApiDeliveryStatus {
  return (
    isObject(value) &&
    typeof value.registration_id === 'string' &&
    typeof value.status === 'string' &&
    typeof value.attempt_count === 'number'
  )
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}
