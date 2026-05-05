import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom'

afterEach(() => {
  cleanup()
})

expect.extend({
  toBeInTheDocument(received) {
    const pass = received && (
      (received.ownerDocument && received.ownerDocument.body.contains(received)) ||
      (received.parentElement && this.isNot(received.parentElement))
    )
    return {
      message: () => `expected element to be in the document`,
      pass
    }
  }
})