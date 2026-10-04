import { readdir, readFile } from 'node:fs/promises'
import { join, relative } from 'node:path'

const sourceDir = new URL('../src/', import.meta.url)
const stylesheetPath = new URL('../src/styles.css', import.meta.url)
const stylesheet = await readFile(stylesheetPath, 'utf8')
const classSelector = /(^|[}\s,])\.[A-Za-z_-][\w-]*/m

if (classSelector.test(stylesheet) || /@media|@keyframes/.test(stylesheet)) {
  throw new Error('Use Tailwind utilities instead of component CSS in src/styles.css')
}

async function findStylesheets(directory) {
  const entries = await readdir(directory, { withFileTypes: true })
  const files = await Promise.all(
    entries.map(async (entry) => {
      const path = join(directory, entry.name)
      if (entry.isDirectory()) return findStylesheets(path)
      return entry.isFile() && path.endsWith('.css') ? [path] : []
    }),
  )
  return files.flat()
}

const stylesheets = await findStylesheets(sourceDir.pathname)
const unexpected = stylesheets.filter((path) => path !== stylesheetPath.pathname)
if (unexpected.length > 0) {
  throw new Error(
    `Unexpected stylesheet(s): ${unexpected.map((path) => relative(sourceDir.pathname, path)).join(', ')}`,
  )
}
