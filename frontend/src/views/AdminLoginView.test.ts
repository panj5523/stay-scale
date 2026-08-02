import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { loginAdmin } from '../api/auth'
import AdminLoginView from './AdminLoginView.vue'

const replace = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ replace }),
  useRoute: () => ({ query: {} }),
}))

vi.mock('../api/auth', () => ({ loginAdmin: vi.fn() }))

beforeEach(() => {
  sessionStorage.clear()
  replace.mockReset()
  vi.mocked(loginAdmin).mockReset().mockResolvedValue({
    access_token: 'signed-token',
    token_type: 'bearer',
    expires_in: 3600,
    user: {
      public_id: 'admin-001',
      username: 'admin',
      display_name: '项目管理员',
      role: 'review_admin',
    },
  })
})

describe('AdminLoginView', () => {
  it('stores the token and opens the review console after login', async () => {
    const wrapper = mount(AdminLoginView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    await wrapper.find('input[type="password"]').setValue('secure-password')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(loginAdmin).toHaveBeenCalledWith('admin', 'secure-password')
    expect(sessionStorage.getItem('stay_scale_admin_token')).toBe('signed-token')
    expect(replace).toHaveBeenCalledWith('/management/reviews')
  })

  it('rejects a short password before calling the API', async () => {
    const wrapper = mount(AdminLoginView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    await wrapper.find('input[type="password"]').setValue('short')
    await wrapper.find('form').trigger('submit')

    expect(loginAdmin).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('至少 8 位密码')
  })
})
