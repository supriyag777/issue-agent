import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { DiffViewer, StatusPill } from './ui'

describe('review safety UI', () => {
  it('renders explicit status text', () => {
    const html = renderToStaticMarkup(<StatusPill tone="warning">DEMO MODE</StatusPill>)
    expect(html).toContain('DEMO MODE')
    expect(html).toContain('pill-warning')
  })

  it('renders additions and removals with distinct classes', () => {
    const html = renderToStaticMarkup(<DiffViewer diff={'@@ -1 +1 @@\n-old\n+new'} />)
    expect(html).toContain('diff-add')
    expect(html).toContain('diff-remove')
  })
})
