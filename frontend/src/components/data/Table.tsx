import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import styles from './Table.module.css'

interface TableProps {
  /** Descricao do conteudo, lida antes da tabela. */
  caption: string
  /** Esconde a caption visualmente sem tirar do DOM. */
  hideCaption?: boolean
  children: ReactNode
}

export function Table({ caption, hideCaption = true, children }: TableProps) {
  return (
    <div className={styles.wrapper}>
      <div className={styles.scroll}>
        <table className={styles.table}>
          <caption className={hideCaption ? 'sr-only' : undefined}>{caption}</caption>
          {children}
        </table>
      </div>
    </div>
  )
}

export function TableHead({ children }: { children: ReactNode }) {
  return <thead>{children}</thead>
}

export function TableBody({ children }: { children: ReactNode }) {
  return <tbody>{children}</tbody>
}

interface TableRowProps {
  children: ReactNode
  /** Linha inteira clicavel: o link real fica na primeira celula. */
  linked?: boolean
}

export function TableRow({ children, linked = false }: TableRowProps) {
  return <tr className={`${styles.row} ${linked ? styles.linkedRow : ''}`.trim()}>{children}</tr>
}

interface TableHeaderCellProps {
  children: ReactNode
  numeric?: boolean
}

/* Sem ordenacao por coluna: nenhuma rota do backend aceita parametro de
   sort, e a lista chega ja ordenada (fila da Ops por prioridade, listas de
   pedido por data). Ordenar so no cliente ordenaria a pagina atual, nao o
   conjunto -- o que engana mais do que ajuda. */
export function TableHeaderCell({ children, numeric = false }: TableHeaderCellProps) {
  return (
    <th scope="col" className={`${styles.headerCell} ${numeric ? styles.numeric : ''}`.trim()}>
      {children}
    </th>
  )
}

interface TableCellProps {
  children: ReactNode
  /** Rotulo da coluna, exibido no modo card (abaixo de md). */
  label: string
  numeric?: boolean
}

export function TableCell({ children, label, numeric = false }: TableCellProps) {
  return (
    <td className={`${styles.cell} ${numeric ? styles.numeric : ''}`.trim()}>
      <span className={styles.label} aria-hidden="true">
        {label}
      </span>
      <span>{children}</span>
    </td>
  )
}

/** Link da primeira celula, que se estende sobre a linha inteira. */
export function TableRowLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link to={to} className={styles.rowLink}>
      {children}
    </Link>
  )
}
