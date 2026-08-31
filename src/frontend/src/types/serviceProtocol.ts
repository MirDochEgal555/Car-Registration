export type ServiceProtocolId = 'tire-change' | 'tire-storage'

export type ServiceProtocol = {
  id: ServiceProtocolId
  title: string
  icon: string
  path: string
}

export const serviceProtocols: readonly ServiceProtocol[] = [
  {
    id: 'tire-change',
    title: 'Reifenwechsel',
    icon: '↻',
    path: '/neu/reifenwechsel',
  },
  {
    id: 'tire-storage',
    title: 'Einlagerung',
    icon: '▣',
    path: '/neu/einlagerung',
  },
]
