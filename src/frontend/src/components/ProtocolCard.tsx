import type { ServiceProtocol } from '../types/serviceProtocol'

type ProtocolCardProps = {
  protocol: ServiceProtocol
}

export function ProtocolCard({ protocol }: ProtocolCardProps) {
  return (
    <article className="protocol-card">
      <span className="protocol-card__icon" aria-hidden="true">
        {protocol.icon}
      </span>
      <div>
        <h2>{protocol.title}</h2>
        <p>{protocol.description}</p>
      </div>
      <span className="protocol-card__status">Startfunktion folgt</span>
    </article>
  )
}
