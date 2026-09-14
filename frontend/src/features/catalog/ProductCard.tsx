import { Box } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { Tag } from '../../components/ui/Tag'
import { formatCurrencyBRL } from '../../lib/utils/format'
import type { CatalogRow } from './catalogRows'
import styles from './ProductCard.module.css'

function sellerLabel(sellerCount: number): string {
  return sellerCount === 1 ? 'em 1 loja' : `em ${sellerCount} lojas`
}

/**
 * Card da grade do catalogo.
 *
 * Mostra so o que ajuda a escolher entre produtos: nome, menor preco e em
 * quantas lojas esta. A descricao fica na PDP -- no card ela ocupa tres
 * linhas e empurra o preco para baixo.
 */
export function ProductCard({ row }: { row: CatalogRow }) {
  const { product, lowestPrice, sellerCount, inStock } = row

  return (
    <li className={styles.item}>
      <Link to={`/catalog/${product.id}`} className={styles.link}>
        <Card interactive className={styles.cardBox}>
          <div className={`${styles.card} ${inStock ? '' : styles.unavailable}`.trim()}>
            <div className={styles.thumb}>
              <Box size={32} aria-hidden="true" />
            </div>
            <h3 className={styles.name}>{product.name}</h3>

            {lowestPrice ? (
              <div className={styles.priceBlock}>
                <span className={styles.priceLabel}>A partir de</span>
                <span className={styles.price}>{formatCurrencyBRL(lowestPrice)}</span>
                <span className={styles.sellers}>{sellerLabel(sellerCount)}</span>
              </div>
            ) : (
              <div className={styles.priceBlock}>
                <Tag tone="muted" dot>
                  Sem estoque
                </Tag>
              </div>
            )}
          </div>
        </Card>
      </Link>
    </li>
  )
}
