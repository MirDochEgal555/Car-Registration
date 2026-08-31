/**
 * Der bewusst kleine, browserseitig genutzte Ausschnitt des FastAPI-Vertrags.
 * Die vollständige Quelle der Wahrheit liegt in app/models/registration.py.
 */
export type ApiRegistrationDraft = {
  id: string
  service_type: 'tire_change' | 'tire_storage'
  service_date: string
  mechanic_id: string
  mechanic_confirmed: boolean
  vehicle: {
    license_plate: string
  }
  tire_sets: Array<{
    role: 'installed' | 'removed' | 'stored'
    tire_set: {
      tire_type?: string
      width_mm?: number
      aspect_ratio?: number
      rim_diameter_inch?: number
      manufacturer?: string
      model?: string
      quantity?: number
      notes?: string
    }
  }>
  tire_inspections: Array<{
    tire_set_role: 'installed' | 'removed' | 'stored'
    tread_front_mm?: number
    tread_rear_mm?: number
  }>
  conditions: Array<{
    tire_set_role: 'installed' | 'removed' | 'stored'
    condition?: string
    position: 'all'
  }>
  tire_change_details?: {
    wheel_change_performed?: boolean
  }
}

export type ApiValidationIssue = {
  field: string
  code: string
  message: string
  status: 'missing' | 'uncertain' | 'invalid' | 'valid'
}

export type ApiValidationResponse = {
  registration: ApiRegistrationDraft
  valid: boolean
  review_required: boolean
  issues: ApiValidationIssue[]
}

export type ApiDeliveryStatus = {
  registration_id: string
  status: 'email_pending' | 'email_sending' | 'email_sent' | 'email_failed'
  recipient?: string | null
  attempt_count: number
  last_error?: string | null
}

export type ApiSendResponse = ApiDeliveryStatus & {
  status: 'email_sent'
  recipient: string
  submitted_at: string
}
