import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from './Button'
import styles from './Pagination.module.css'

interface PaginationProps {
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
}

/** Extraido da duplicacao que existia em cada tela de lista paginada. */
export function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  const pageCount = Math.max(1, Math.ceil(total / pageSize))
  const hasNextPage = page * pageSize < total

  return (
    <nav className={styles.pagination} aria-label="Paginação">
      <Button
        type="button"
        variant="secondary"
        size="sm"
        disabled={page === 1}
        onClick={() => onPageChange(page - 1)}
      >
        <ChevronLeft size={16} aria-hidden="true" />
        Anterior
      </Button>
      <span className={styles.status} aria-live="polite">
        Página {page} de {pageCount}
      </span>
      <Button
        type="button"
        variant="secondary"
        size="sm"
        disabled={!hasNextPage}
        onClick={() => onPageChange(page + 1)}
      >
        Próxima
        <ChevronRight size={16} aria-hidden="true" />
      </Button>
    </nav>
  )
}
