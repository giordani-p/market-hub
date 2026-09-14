import { useId, useRef, type KeyboardEvent, type ReactNode } from 'react'
import styles from './Tabs.module.css'

export interface TabItem {
  id: string
  label: string
  content: ReactNode
}

interface TabsProps {
  items: TabItem[]
  selectedId: string
  onSelect: (id: string) => void
  label: string
}

/** Tabs com navegacao por seta, como o padrao WAI-ARIA espera. */
export function Tabs({ items, selectedId, onSelect, label }: TabsProps) {
  const baseId = useId()
  const listRef = useRef<HTMLDivElement>(null)

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    const currentIndex = items.findIndex((item) => item.id === selectedId)
    let nextIndex: number | null = null
    if (event.key === 'ArrowRight') {
      nextIndex = (currentIndex + 1) % items.length
    } else if (event.key === 'ArrowLeft') {
      nextIndex = (currentIndex - 1 + items.length) % items.length
    } else if (event.key === 'Home') {
      nextIndex = 0
    } else if (event.key === 'End') {
      nextIndex = items.length - 1
    }
    if (nextIndex === null) {
      return
    }
    event.preventDefault()
    const next = items[nextIndex]
    onSelect(next.id)
    listRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]')[nextIndex]?.focus()
  }

  const selected = items.find((item) => item.id === selectedId) ?? items[0]

  return (
    <div>
      <div
        className={styles.tabList}
        role="tablist"
        aria-label={label}
        ref={listRef}
        onKeyDown={handleKeyDown}
      >
        {items.map((item) => {
          const isSelected = item.id === selected.id
          return (
            <button
              key={item.id}
              type="button"
              role="tab"
              id={`${baseId}-tab-${item.id}`}
              aria-selected={isSelected}
              aria-controls={`${baseId}-panel-${item.id}`}
              tabIndex={isSelected ? 0 : -1}
              className={`${styles.tab} ${isSelected ? styles.tabSelected : ''}`.trim()}
              onClick={() => onSelect(item.id)}
            >
              {item.label}
            </button>
          )
        })}
      </div>
      <div
        className={styles.panel}
        role="tabpanel"
        id={`${baseId}-panel-${selected.id}`}
        aria-labelledby={`${baseId}-tab-${selected.id}`}
        tabIndex={0}
      >
        {selected.content}
      </div>
    </div>
  )
}
