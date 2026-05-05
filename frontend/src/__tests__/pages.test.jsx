import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider } from '../context/ThemeContext'
import LoginPage from '../pages/LoginPage'

vi.mock('axios', () => ({
  default: {
    post: vi.fn(() => Promise.resolve({ data: { status: 'ok' } })),
    get: vi.fn(() => Promise.resolve({ data: {} }))
  }
}))

const renderWithTheme = (component) => {
  return render(
    <BrowserRouter>
      <ThemeProvider>
        {component}
      </ThemeProvider>
    </BrowserRouter>
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders username input', () => {
    renderWithTheme(<LoginPage />)
    expect(screen.getByPlaceholderText(/tu usuario/i)).toBeDefined()
  })

  it('renders password input', () => {
    renderWithTheme(<LoginPage />)
    expect(screen.getByPlaceholderText('••••••••')).toBeDefined()
  })

  it('renders submit button', () => {
    renderWithTheme(<LoginPage />)
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeDefined()
  })

  })