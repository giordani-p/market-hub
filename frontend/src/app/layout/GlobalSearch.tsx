import { Search } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import type { UserRole } from '../../types/auth'
import styles from './GlobalSearch.module.css'

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

/** Lista de pedidos de cada papel, destino da busca por ID. */
const ORDER_LIST_PATH: Record<UserRole, string | null> = {
  buyer: null,
  seller: '/seller/orders',
  ops: '/ops/order-items',
}

const PLACEHOLDER: Record<UserRole, string> = {
  buyer: 'Buscar produto',
  seller: 'Buscar produto ou colar ID do item',
  ops: 'Buscar produto ou colar ID do item',
}

/**
 * Busca do header.
 *
 * Nao ha endpoint de busca global no backend, entao ela despacha para a
 * tela que ja sabe filtrar: ID completo vai para a lista de pedidos do
 * papel; qualquer outro termo vai para o catalogo.
 */
export function GlobalSearch({ role }: { role: UserRole }) {
  const navigate = useNavigate()
  const [term, setTerm] = useState('')

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const value = term.trim()
    if (!value) {
      return
    }
    const orderListPath = ORDER_LIST_PATH[role]
    if (orderListPath && UUID_PATTERN.test(value)) {
      navigate(`${orderListPath}?order_item_id=${value}`)
      return
    }
    navigate(`/catalog?q=${encodeURIComponent(value)}`)
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} role="search">
      <Search size={16} className={styles.icon} aria-hidden="true" />
      <label className="sr-only" htmlFor="global-search">
        Buscar
      </label>
      <input
        id="global-search"
        className={styles.input}
        type="search"
        value={term}
        onChange={(event) => setTerm(event.target.value)}
        placeholder={PLACEHOLDER[role]}
      />
    </form>
  )
}
