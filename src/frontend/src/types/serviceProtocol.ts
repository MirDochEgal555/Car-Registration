import type { WorkshopProcessType } from './workshopProcess'

export type ServiceProtocolId = WorkshopProcessType

export type ServiceProtocol = {
  id: ServiceProtocolId
  title: string
  icon: string
}

export const serviceProtocols: readonly ServiceProtocol[] = [
  {
    id: 'tire_change',
    title: 'Reifenwechsel',
    icon: '↻',
  },
  {
    id: 'tire_storage',
    title: 'Einlagerung',
    icon: '▣',
  },
]
