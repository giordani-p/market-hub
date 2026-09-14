import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * Leva o foco para o titulo da pagina a cada navegacao.
 *
 * Sem isso o foco fica no link clicado e quem usa teclado ou leitor de tela
 * continua no menu depois de trocar de tela.
 */
export function useRouteFocus() {
  const { pathname } = useLocation()

  useEffect(() => {
    const title = document.getElementById('page-title')
    const target = title ?? document.getElementById('main-content')
    target?.focus()
  }, [pathname])
}
