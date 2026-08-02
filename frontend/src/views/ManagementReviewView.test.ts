import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { decideReviewTask, getReviewTasks } from '../api/managementReview'
import type { ReviewTask } from '../types/managementReview'
import ManagementReviewView from './ManagementReviewView.vue'

vi.mock('../api/managementReview', () => ({
  getReviewTasks: vi.fn(),
  decideReviewTask: vi.fn(),
}))

const task: ReviewTask = {
  record_id: 12,
  batch_id: 4,
  platform_code: 'tujia',
  external_id: 'TJ-REVIEW-1',
  listing_name: '云栖设计师庭院',
  review_status: 'pending',
  match_method: 'weighted_similarity',
  match_score: '0.8230',
  match_decision: 'review_required',
  evidence: { name_similarity: 0.88, distance_m: 120 },
  normalized_payload: {
    city: '大理市',
    district: '大理镇',
    address: '才村示范地址',
  },
  candidate: {
    public_id: 'DL_000001',
    name: '云栖·洱海庭院民宿',
    city: '大理市',
    district: '大理镇',
    address: '才村示范地址1号',
  },
  created_at: '2026-08-02T02:00:00',
  reviewed_at: null,
}

beforeEach(() => {
  vi.mocked(getReviewTasks).mockReset().mockResolvedValue({
    items: [task],
    total: 1,
    page: 1,
    page_size: 50,
  })
  vi.mocked(decideReviewTask).mockReset().mockResolvedValue({
    audit_id: 'audit-001',
    record_id: 12,
    review_status: 'approved',
    target_canonical_public_id: 'DL_000001',
    reviewer_name: '项目管理员',
    reason: '名称和地址证据一致',
    reviewed_at: '2026-08-02T03:00:00',
  })
})

function mountView() {
  return mount(ManagementReviewView, {
    global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
  })
}

describe('ManagementReviewView', () => {
  it('loads and displays pending review evidence', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(getReviewTasks).toHaveBeenCalledWith('pending')
    expect(wrapper.text()).toContain('云栖设计师庭院')
    await wrapper.find('.task-card').trigger('click')
    expect(wrapper.text()).toContain('DL_000001')
    expect(wrapper.text()).toContain('才村示范地址1号')
  })

  it('approves a selected task with an audit reason', async () => {
    const wrapper = mountView()
    await flushPromises()
    await wrapper.find('.task-card').trigger('click')
    await wrapper.find('textarea').setValue('名称和地址证据一致')
    const approve = wrapper.findAll('button').find((button) => button.text() === '通过并关联')
    await approve?.trigger('click')
    await flushPromises()

    expect(decideReviewTask).toHaveBeenCalledWith(12, {
      action: 'approve',
      reviewerName: '项目管理员',
      reason: '名称和地址证据一致',
      targetCanonicalPublicId: 'DL_000001',
    })
  })
})
