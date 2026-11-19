# FastAPI docs structure notes

Source repository: https://github.com/fastapi/fastapi
Verified English docs folder in the source clone: `docs/en/docs`
Source commit: `05e6df7e906c3decba377c37548019973f40bf15`
Copied to: `data/raw/` (159 Markdown files, 411 files total)

Counting method: a heading is a line starting with `#` outside a fenced code block;
a fenced code block is a pair of lines starting with three backticks or three
tilde characters. Headings inside
code fences (for example Dockerfile comments) are not counted.

## Ten sampled files

### 1. `data/raw/tutorial/first-steps.md`

- Headings: 27
- Fenced code blocks: yes, 14
- Admonition / site-specific syntax found (exact quotes):
  - Heading anchor: `# First Steps { #first-steps }`
  - Source include: `{* ../../docs_src/first_steps/tutorial001.py *}`
  - Admonition: `/// tip` ... `///`, and `/// note | Technical Details` ... `///`
  - Terminal HTML wrapper: `<div class="termy">` ... `</div>`
  - Highlighted fence opener: ```` ```hl_lines="4" ````

### 2. `data/raw/tutorial/handling-errors.md`

- Headings: 13
- Fenced code blocks: yes, 8
- Admonition / site-specific syntax found (exact quotes):
  - Heading anchor: `# Handling Errors { #handling-errors }`
  - Source include with highlight: `{* ../../docs_src/handling_errors/tutorial001.py hl[1] *}`
  - Admonition: `/// tip` ... `///`, and `/// note | Technical Details` ... `///`

### 3. `data/raw/advanced/advanced-dependencies.md`

- Headings: 17
- Fenced code blocks: yes, 2
- Admonition / site-specific syntax found (exact quotes):
  - Heading anchor: `# Advanced Dependencies { #advanced-dependencies }`
  - Source include with highlight: `{* ../../docs_src/dependencies/tutorial011.py hl[12] *}`
  - Admonition: `/// tip` ... `///`, `/// note` ... `///`, and `/// note | Technical Details`

### 4. `data/raw/advanced/behind-a-proxy.md`

- Headings: 15
- Fenced code blocks: yes, 15
- Admonition / site-specific syntax found (exact quotes):
  - Heading anchor: `# Behind a Proxy { #behind-a-proxy }`
  - Admonition: `/// note | Technical Details` ... `///`, and `/// tip` ... `///`
  - Terminal HTML wrapper: `<div class="termy">` ... `</div>`
  - Source include with highlight: `{* ../../docs_src/behind_a_proxy/tutorial001_01.py hl[6] *}`
  - Diagram fence opener: ```` ```mermaid ````
  - Highlighted fence opener: ```` ```JSON hl_lines="4-8" ````

### 5. `data/raw/how-to/testing-database.md`

- Headings: 1
- Fenced code blocks: no
- Admonition / site-specific syntax found (exact quotes):
  - Only a heading anchor: `# Testing a Database { #testing-a-database }`
  - Otherwise plain Markdown with external links; no admonitions or includes.

### 6. `data/raw/how-to/custom-docs-ui-assets.md`

- Headings: 15
- Fenced code blocks: yes, 4
- Admonition / site-specific syntax found (exact quotes):
  - Heading anchor: `# Custom Docs UI Static Assets (Self-Hosting) { #custom-docs-ui-static-assets-self-hosting }`
  - Source include with highlight: `{* ../../docs_src/custom_docs_ui/tutorial001.py hl[8] *}`
  - Admonition: `/// tip` ... `///`

### 7. `data/raw/deployment/docker.md`

- Headings: 37
- Fenced code blocks: yes, 18
- Admonition / site-specific syntax found (exact quotes):
  - Heading anchor: `# FastAPI in Containers - Docker { #fastapi-in-containers-docker }`
  - Admonition: `/// tip` ... `///`, and `/// note` ... `///`
  - Collapsible HTML: `<details>`, `<summary>Dockerfile Preview 👀</summary>`, `</details>`
  - Terminal HTML wrapper: `<div class="termy">` ... `</div>`
  - Annotated fence opener: ```` ```{ .dockerfile .annotate } ````

### 8. `data/raw/deployment/https.md`

- Headings: 15
- Fenced code blocks: no
- Admonition / site-specific syntax found (exact quotes):
  - Heading anchor: `# About HTTPS { #about-https }`
  - Admonition: `/// tip` ... `///`
  - Absolute image path: `<img src="/img/deployment/https/https01.drawio.svg">`

### 9. `data/raw/reference/fastapi.md`

- Headings: 1
- Fenced code blocks: yes, 1
- Admonition / site-specific syntax found (exact quotes):
  - Plain heading (no anchor): `# \`FastAPI\` class`
  - mkdocstrings directive: `::: fastapi.FastAPI`, followed by `    options:` and `        members:`
  - Code fence opener: ```` ```python ````

### 10. `data/raw/about/index.md`

- Headings: 1
- Fenced code blocks: no
- Admonition / site-specific syntax found (exact quotes):
  - Heading anchor: `# About { #about }`
  - Otherwise one short paragraph of plain text; no admonitions or includes.

## What Phase 1 must clean or handle

- Strip site-specific heading anchors such as `{ #first-steps }` while keeping the heading text and hierarchy as chunk metadata.
- Decide how to resolve or drop `{* ../../docs_src/... hl[1] *}` includes and fence annotations such as ```` ```hl_lines="4" ```` and ```` ```{ .dockerfile .annotate } ````.
- Remove or flatten site-only HTML (`<div class="termy">`, `<details>` / `<summary>`, `<img src="/img/...">`) and non-text `mermaid` fences without losing useful prose.
- Convert `/// tip` and `/// note | Technical Details` admonitions into plain text or structured notes that stay attached to the surrounding section.
- Keep a stable citation (source path plus heading or anchor) for every chunk, and handle near-empty stubs (`how-to/testing-database.md`, `about/index.md`) and directive-only pages (`reference/fastapi.md`) explicitly.
