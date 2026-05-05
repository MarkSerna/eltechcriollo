import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider } from '../context/ThemeContext'
import NewsCard from '../components/NewsCard'

const renderWithTheme = (component) => {
  return render(
    <BrowserRouter>
      <ThemeProvider>
        {component}
      </ThemeProvider>
    </BrowserRouter>
  )
}

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

  it('renders card element', () => {
    render(<NewsCard article={mockArticle} />)
    const card = screen.getByText('Test Article').closest('div')
    expect(card).toBeDefined()
  })
})