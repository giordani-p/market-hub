import type { ReactNode } from 'react'
import styles from './DetailList.module.css'

export interface DetailEntry {
  term: string
  value: ReactNode
}

/** Par rotulo/valor das telas de detalhe, que antes cada tela montava a mao. */
export function DetailList({ entries }: { entries: DetailEntry[] }) {
  return (
    <dl className={styles.detailList}>
      {entries.map((entry) => (
        <div key={entry.term} style={{ display: 'contents' }}>
          <dt className={styles.term}>{entry.term}</dt>
          <dd className={styles.definition}>{entry.value}</dd>
        </div>
      ))}
    </dl>
  )
}
