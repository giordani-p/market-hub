import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  TableRowLink,
} from './Table'

function renderTable() {
  return render(
    <MemoryRouter>
      <Table caption="Itens de pedido">
        <TableHead>
          <TableRow>
            <TableHeaderCell>Produto</TableHeaderCell>
            <TableHeaderCell numeric>Valor</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow linked>
            <TableCell label="Produto">
              <TableRowLink to="/seller/orders/item-1">Tenis Runner</TableRowLink>
            </TableCell>
            <TableCell label="Valor" numeric>
              R$ 199,90
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </MemoryRouter>,
  )
}

describe('Table', () => {
  it('exposes the caption and column headers to assistive technology', () => {
    renderTable()

    expect(screen.getByRole('table', { name: 'Itens de pedido' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Produto' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Valor' })).toBeInTheDocument()
  })

  it('keeps a real link in the row, not a click handler on the tr', () => {
    renderTable()

    const row = screen.getAllByRole('row')[1]
    expect(within(row).getByRole('link', { name: 'Tenis Runner' })).toHaveAttribute(
      'href',
      '/seller/orders/item-1',
    )
  })

  it('repeats the column label in each cell, for the card layout', () => {
    renderTable()

    const row = screen.getAllByRole('row')[1]
    // Os rotulos ficam ocultos no desktop e aparecem quando a tabela vira
    // lista de cards abaixo de md.
    expect(within(row).getByText('Valor')).toBeInTheDocument()
  })
})
