import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const apiModulePath = new URL('../src/api/index.js', import.meta.url)
const requestModulePath = new URL('../src/api/request.js', import.meta.url)

test('resumeApi exposes list, detail, and blob download endpoint contracts', async () => {
  const source = await readFile(apiModulePath, 'utf8')

  assert.match(source, /export const resumeApi\s*=\s*\{/)
  assert.match(source, /list:\s*\(params\)\s*=>\s*api\.get\('\/resumes',\s*\{\s*params\s*\}\)/)
  assert.match(source, /detail:\s*\(id\)\s*=>\s*api\.get\(`\/resumes\/\$\{id\}`\)/)
  assert.match(source, /download:\s*\(id\)\s*=>\s*api\.get\(`\/resumes\/\$\{id\}\/download`,\s*\{\s*responseType:\s*'blob'\s*\}\)/)
})

test('response interceptor returns blob downloads before parsing API envelopes', async () => {
  const source = await readFile(requestModulePath, 'utf8')

  assert.match(source, /if\s*\(res\.config\.responseType\s*===\s*['"]blob['"]\)\s*return res/)
})
