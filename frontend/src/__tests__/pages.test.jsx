import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import LoginPage from '../pages/LoginPage'

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}))

const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders login form', () => {
    renderWithRouter(<LoginPage />)
    expect(screen.getByPlaceholderText(/usuario/i)).toBeDefined()
    expect(screen.getByPlaceholderText(/contraseña/i)).toBeDefined()
  })

  it('renders login button', () => {
    renderWithRouter(<LoginPage />)
    expect(screen.getByRole('button', { name: /ingresar/i })).toBeDefined()
  })

  it('has title', () => {
    renderWithRouter(<LoginPage />)
    expect(screen.getByText(/el tech criollo/i)).toBeDefined()
  })
})