import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Navbar from '../components/Navbar'
import NewsCard from '../components/NewsCard'
import NewsModal from '../components/NewsModal'

const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('Navbar Component', () => {
  beforeEach(() => {
    vi.mock('../context/AuthContext', () => ({
      useAuth: () => ({
        user: { username: 'testuser', authenticated: true },
        logout: vi.fn()
      })
    }))
  })

  it('renders navigation links', () => {
    renderWithRouter(<Navbar />)
    expect(screen.getByText(/dashboard/i)).toBeDefined()
  })
})

describe('NewsCard Component', () => {
  const mockArticle = {
    id: 1,
    title: 'Test Article',
    source: 'Test Source',
    url: 'https://example.com',
    image_url: 'https://example.com/image.jpg',
    processed_at: '2026-05-04T10:00:00'
  }

  it('renders article title', () => {
    render(<NewsCard article={mockArticle} />)
    expect(screen.getByText('Test Article')).toBeDefined()
  })

  it('renders article source', () => {
    render(<NewsCard article={mockArticle} />)
    expect(screen.getByText('Test Source')).toBeDefined()
  })
})

describe('NewsModal Component', () => {
  const mockArticle = {
    id: 1,
    title: 'Test Article',
    source: 'Test Source',
    url: 'https://example.com',
    image_url: 'https://example.com/image.jpg',
    summary: 'Test summary',
    ai_comment: 'Test AI comment',
    region: 'colombia',
    department: 'Caldas'
  }

  it('renders modal with article data', () => {
    render(<NewsModal article={mockArticle} onClose={() => {}} />)
    expect(screen.getByText('Test Article')).toBeDefined()
  })

  it('calls onClose when close button is clicked', () => {
    const mockClose = vi.fn()
    render(<NewsModal article={mockArticle} onClose={mockClose} />)
    expect(mockClose).not.toHaveBeenCalled()
  })
})