export type ServiceProtocolId = 'tire-change' | 'tire-storage'

export type ServiceProtocol = {
  id: ServiceProtocolId
  title: string
  description: string
  icon: string
}

export const serviceProtocols: readonly ServiceProtocol[] = [
  {
    id: 'tire-change',
    title: 'Reifenwechsel',
    description: 'Montierte und demontierte Räder erfassen.',
    icon: '↻',
  },
  {
    id: 'tire-storage',
    title: 'Reifeneinlagerung',
    description: 'Einen Radsatz für die Einlagerung dokumentieren.',
    icon: '▣',
  },
]
