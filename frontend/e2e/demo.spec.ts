import { expect, test } from '@playwright/test'

test('student completes the grounded learning flow', async ({ page }) => {
  await page.goto('/login')
  await page.getByRole('button', { name: '登录' }).click()
  await expect(page.getByRole('heading', { name: /你好/ })).toBeVisible()
  await expect(page.getByText('人工智能应用开发基础')).toBeVisible()
  await page.getByText('人工智能应用开发基础').click()
  await expect(page.getByText('RAG基础.docx')).toBeVisible()

  await page.getByRole('tab', { name: 'AI 问答' }).click()
  await page.getByPlaceholder('只依据当前课程资料回答…').fill('RAG 包含哪些主要阶段？')
  await page.getByRole('button', { name: '发送' }).click()
  await expect(page.getByText(/根据课程资料/)).toBeVisible({ timeout: 30_000 })
  await expect(page.getByText(/\[S1\]/).first()).toBeVisible()

  await page.getByRole('tab', { name: '课程摘要' }).click()
  await page.getByRole('button', { name: '生成课程摘要' }).click()
  await expect(page.getByText('核心知识点').first()).toBeVisible()

  await page.getByRole('tab', { name: '智能测验' }).click()
  await page.getByRole('button', { name: '生成 5 道题' }).click()
  await expect(page.getByText(/RAG 的核心流程通常包含哪三个阶段/).first()).toBeVisible()
})
