import { expect, test } from '@playwright/test'

test.describe('BaiCao mainline', () => {
  test('home, search, graph, chat and verification are reachable', async ({ page }) => {
    await page.goto('/')

    await expect(page).toHaveTitle(/白草药坛/)
    await expect(page.getByText('欢迎使用白草药坛')).toBeVisible()
    await expect(page.getByRole('heading', { name: '知识搜索' })).toBeVisible()
    await expect(page.getByRole('heading', { name: '图谱浏览' })).toBeVisible()

    await page.goto('/search')
    await expect(page.getByRole('heading', { name: '搜索' })).toBeVisible()
    await page.getByPlaceholder('输入药材名称搜索...').fill('人参')
    await page.getByRole('button', { name: /搜\s*索/ }).click()
    await expect(page.getByText('人参', { exact: true })).toBeVisible()

    await page.getByText('人参', { exact: true }).click()
    await expect(page.getByRole('heading', { name: /人参 的知识图谱/ })).toBeVisible()
    await expect(page.getByText('节点详情')).toBeVisible()

    await page.goto('/chat')
    await expect(page.getByRole('heading', { name: '智能问答' })).toBeVisible()
    await page.getByPlaceholder('输入您的问题，例如：陈皮有什么功效？').fill('人参有什么功效？')
    await page.getByRole('button', { name: /发送/ }).click()
    await expect(page.getByText('关于「人参」的信息：')).toBeVisible()

    await page.goto('/verification')
    await expect(page.getByRole('heading', { name: '验证管理' })).toBeVisible()
    await expect(page.getByRole('button', { name: '申请验证' })).toBeVisible()
  })
})
