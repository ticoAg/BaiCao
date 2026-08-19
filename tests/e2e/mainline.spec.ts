import { expect, test } from '@playwright/test'

test.describe('BaiCao mainline', () => {
  test('home, search, graph, chat and verification are reachable', async ({ page }) => {
    await page.goto('/')

    await expect(page).toHaveTitle(/白草药坛/)
    await expect(page.getByRole('heading', { name: '白草药坛', level: 1 })).toBeVisible()
    await expect(page.getByRole('heading', { name: '知识搜索' })).toBeVisible()
    await expect(page.getByRole('heading', { name: '图谱浏览' })).toBeVisible()

    await page.goto('/search')
    await expect(page.getByRole('heading', { name: '搜索' })).toBeVisible()
    await page.getByRole('textbox').fill('人参')
    await page.getByRole('button', { name: /搜\s*索/ }).click()
    await expect(page.getByText('人参', { exact: true })).toBeVisible()

    await page.getByText('人参', { exact: true }).click()
    await expect(page.getByText('当前图谱', { exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: '打开查询器' })).toBeVisible()

    const finalPayload = {
      answer: '陈皮可理气健脾。',
      provider_reasoning: [],
      evidence: [{
        entity_id: 'herb-chenpi',
        evidence_id: 'ev-chenpi',
        snippet: '陈皮理气健脾。',
        source_id: 'src-pharmacopoeia',
        source_name: '中国药典（2020年版）',
      }],
      related_nodes: [],
      related_edges: [],
      subgraph_meta: {
        center_node_id: null,
        actual_depth: 0,
        fallback_used: false,
        node_count: 0,
        edge_count: 0,
      },
      reasoning_trace: [],
      tool_calls: [],
      session_id: 'e2e-citation',
    }
    await page.route('**/chat/stream', async (route) => {
      await route.fulfill({
        contentType: 'text/event-stream',
        body: [
          'event: session',
          'data: {"session_id":"e2e-citation","turn_id":"turn-1"}',
          '',
          'event: answer_chunk',
          'data: {"text":"陈皮可理气健脾。"}',
          '',
          'event: final',
          `data: ${JSON.stringify(finalPayload)}`,
          '',
          '',
        ].join('\n'),
      })
    })
    await page.route('**/provenance/entity/herb-chenpi/lineage', async (route) => {
      await route.fulfill({ json: {
        entity: { id: 'herb-chenpi', name: '陈皮', status: 'verified' },
        evidence: { id: 'ev-chenpi', content: '陈皮理气健脾。', source_name: '中国药典（2020年版）', status: 'verified' },
        source: { id: 'src-pharmacopoeia', name: '中国药典（2020年版）', status: 'verified' },
      } })
    })
    await page.route('**/provenance/entity/herb-chenpi/evidence', async (route) => {
      await route.fulfill({ json: { evidence: [], count: 0 } })
    })
    await page.route('**/provenance/entity/herb-chenpi/completeness', async (route) => {
      await route.fulfill({ json: {
        entity: { id: 'herb-chenpi', name: '陈皮', status: 'verified' },
        evidence: { id: 'ev-chenpi', content: '陈皮理气健脾。', source_name: '中国药典（2020年版）', status: 'verified' },
        source: { id: 'src-pharmacopoeia', name: '中国药典（2020年版）', status: 'verified' },
        has_evidence: true,
        has_source: true,
        chain_complete: true,
      } })
    })

    await page.goto('/chat')
    await expect(page.getByRole('heading', { name: '智能问答' })).toBeVisible()
    await page.getByPlaceholder('输入您的问题，例如：陈皮有什么功效？').fill('人参有什么功效？')
    await page.getByRole('button', { name: /发送/ }).click()
    await expect(page.getByText('陈皮理气健脾。')).toBeVisible()
    await expect(page.getByText('中国药典（2020年版）').first()).toBeVisible()
    await page.getByRole('button', { name: '查看溯源 herb-chenpi' }).click()
    await expect(page.getByText('证据溯源：herb-chenpi')).toBeVisible()

    await page.goto('/verification')
    await expect(page.getByRole('heading', { name: '验证管理' })).toBeVisible()
    await expect(page.getByRole('button', { name: '申请验证' })).toBeVisible()
  })
})
