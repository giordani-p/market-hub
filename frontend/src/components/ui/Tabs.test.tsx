import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'
import { Tabs } from './Tabs'

function Harness() {
  const [selected, setSelected] = useState('conversation')
  return (
    <Tabs
      label="Comunicação do item"
      selectedId={selected}
      onSelect={setSelected}
      items={[
        { id: 'conversation', label: 'Conversa', content: <p>Thread com o comprador</p> },
        { id: 'support', label: 'Suporte interno', content: <p>Log interno</p> },
      ]}
    />
  )
}

describe('Tabs', () => {
  it('shows only the selected panel', () => {
    render(<Harness />)

    expect(screen.getByRole('tab', { name: 'Conversa' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText('Thread com o comprador')).toBeInTheDocument()
    expect(screen.queryByText('Log interno')).not.toBeInTheDocument()
  })

  it('moves between tabs with the arrow keys', async () => {
    const user = userEvent.setup()
    render(<Harness />)

    await user.click(screen.getByRole('tab', { name: 'Conversa' }))
    await user.keyboard('{ArrowRight}')

    const support = screen.getByRole('tab', { name: 'Suporte interno' })
    expect(support).toHaveAttribute('aria-selected', 'true')
    expect(support).toHaveFocus()
    expect(screen.getByText('Log interno')).toBeInTheDocument()
  })
})
