import type { Offer, Product } from '../../types/catalog'

/**
 * Linha do catalogo: um produto mais o que foi agregado das ofertas dele.
 *
 * Agregacao e apresentacao, nao regra de dominio -- preco, estoque e
 * disponibilidade vem prontos do backend. Aqui so se resume o que ja
 * chegou, para o card poder comparar produtos.
 */
export interface CatalogRow {
  product: Product
  /** Menor preco entre as ofertas compraveis. `null` quando nao ha nenhuma. */
  lowestPrice: string | null
  highestPrice: string | null
  /** Lojas distintas com oferta comprável. */
  sellerCount: number
  offerCount: number
  inStock: boolean
}

function isPurchasable(offer: Offer): boolean {
  return offer.available && offer.stock > 0
}

/**
 * Cruza produtos e ofertas em uma passada.
 *
 * O cruzamento morava dentro do `.map` da tela e era refeito a cada
 * render, duas vezes, em O(produtos x ofertas).
 */
export function deriveCatalogRows(products: Product[], offers: Offer[]): CatalogRow[] {
  const purchasableByProduct = new Map<string, Offer[]>()
  for (const offer of offers) {
    if (!isPurchasable(offer)) {
      continue
    }
    const current = purchasableByProduct.get(offer.product_id)
    if (current) {
      current.push(offer)
    } else {
      purchasableByProduct.set(offer.product_id, [offer])
    }
  }

  return products.map((product) => {
    const purchasable = purchasableByProduct.get(product.id) ?? []
    if (purchasable.length === 0) {
      return {
        product,
        lowestPrice: null,
        highestPrice: null,
        sellerCount: 0,
        offerCount: 0,
        inStock: false,
      }
    }

    let lowest = purchasable[0]
    let highest = purchasable[0]
    const sellers = new Set<string>()
    for (const offer of purchasable) {
      sellers.add(offer.seller_id)
      if (Number(offer.price) < Number(lowest.price)) {
        lowest = offer
      }
      if (Number(offer.price) > Number(highest.price)) {
        highest = offer
      }
    }

    return {
      product,
      lowestPrice: lowest.price,
      highestPrice: highest.price,
      sellerCount: sellers.size,
      offerCount: purchasable.length,
      inStock: true,
    }
  })
}
