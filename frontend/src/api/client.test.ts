import { describe, expect, it } from 'vitest'
import { errorMessage } from './client'

describe('API error normalization', () => {
  it('prefers the stable message returned by the backend', () => {
    expect(errorMessage({ response: { data: { code: 'COURSE_FORBIDDEN', message: '无课程访问权限' } } }))
      .toBe('无课程访问权限')
  })

  it('falls back to network errors and a user-friendly default', () => {
    expect(errorMessage({ message: 'Network Error' })).toBe('Network Error')
    expect(errorMessage({})).toBe('操作失败，请稍后重试')
  })
})
