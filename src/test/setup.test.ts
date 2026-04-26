import { describe, it, expect } from 'vitest'

describe('test setup', () => {
  it('has window.wenforge mocked', () => {
    expect(window.wenforge).toBeDefined()
    expect(window.wenforge.listProjects).toBeDefined()
  })

  it('mock returns expected values', async () => {
    const projects = await window.wenforge.listProjects()
    expect(projects).toEqual([])
  })
})
