import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import EnvironmentStatusView from './EnvironmentStatusView.vue'
import { getReadiness } from '../api/health'

vi.mock('../api/health', () => ({
  getReadiness: vi.fn(),
}))

const mockedGetReadiness = vi.mocked(getReadiness)

describe('EnvironmentStatusView', () => {
  beforeEach(() => {
    mockedGetReadiness.mockReset()
  })

  it('shows the service readiness returned by FastAPI', async () => {
    mockedGetReadiness.mockResolvedValue({
      status: 'ready',
      service: 'Stay Scale API',
      version: '0.1.0',
      checks: {
        database: { status: 'up', message: 'MySQL 连接正常' },
        redis: { status: 'up', message: 'Redis 连接正常' },
      },
      timestamp: '2026-07-27T12:00:00Z',
    })

    const wrapper = mount(EnvironmentStatusView)
    await flushPromises()

    expect(wrapper.text()).toContain('MySQL 连接正常')
    expect(wrapper.text()).toContain('Redis 连接正常')
    expect(wrapper.text()).toContain('FastAPI 0.1.0')
  })

  it('shows a useful message when FastAPI cannot be reached', async () => {
    mockedGetReadiness.mockRejectedValue(new Error('network error'))

    const wrapper = mount(EnvironmentStatusView)
    await flushPromises()

    expect(wrapper.text()).toContain('FastAPI 未连接')
    expect(wrapper.text()).toContain('8000 端口')
  })
})
