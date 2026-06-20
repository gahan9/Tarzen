# Competency Map, AI-Augmented Workflow & Sources

The breadth a senior full-stack developer draws on, the modern AI-assisted way of
working, and the sources this skill distills. Load for stack-selection context,
mentoring/learning-path questions, or to ground a recommendation.

## Competency map

A senior generalist is fluent across these areas and knows *when each matters* —
not an expert in all simultaneously, but able to fill any gap on the team.

**Foundations**

- HTML5 (semantic, forms, accessibility, SEO basics), CSS3 (Flexbox, Grid,
  responsive, animations, variables), and JavaScript (ES6+, async/await, closures,
  modules, the DOM, Web APIs: Fetch, storage).
- TypeScript for type-safe apps at scale.

**Frontend**

- A component framework (React default; Vue/Svelte/Angular transferable).
- State management escalated to need (local → context → query cache → global
  store), routing, forms + schema validation, styling (Tailwind/CSS Modules),
  performance (code-split, memo, virtualize), accessibility.

**Backend**

- A server runtime + framework: Node/Express (or Fastify/NestJS) **and/or**
  Python/Django (or FastAPI/Flask).
- RESTful API design (and awareness of GraphQL/tRPC/gRPC), middleware, error
  handling, auth (sessions, JWT, OAuth/OIDC), real-time (WebSockets), security
  (OWASP Top 10), caching, background jobs/queues.

**Data**

- Relational (PostgreSQL) + an ORM, schema design, indexing, transactions,
  migrations; NoSQL (MongoDB) modeling; Redis for cache/sessions; query tuning.

**Delivery & craft**

- Git/GitHub workflow, package managers, bundlers (Vite/Webpack), linting/format
  (ESLint/Prettier, ruff/black).
- Testing (unit/integration/E2E), CI/CD, Docker, cloud/PaaS deployment,
  monitoring and logging.
- System design, debugging, security mindset, and the soft skills:
  communication, code review, estimation, documentation.

## Suggested learning path (for mentoring)

Order matters; each stage builds on the last. Indicative durations assume
consistent practice for someone newer to the area.

1. **Web foundations** — HTML, CSS, JavaScript (2-3 months).
2. **Tooling & version control** — Git/GitHub, npm, VS Code, ESLint/Prettier
   (2-3 weeks).
3. **Frontend framework** — React + TypeScript, hooks, state, routing, forms
   (2-3 months).
4. **Backend** — Node/Express or Python/Django, REST, auth, security
   (2-3 months).
5. **Database** — PostgreSQL/MongoDB, modeling, ORM, indexing (1-2 months).
6. **Full-stack integration** — wire FE↔BE, auth flows, file upload, real-time
   (2-3 months).
7. **Deployment & DevOps** — CI/CD, Docker, a deploy platform (1-2 months).
8. **Testing & QA** — Jest/Vitest/pytest, RTL, Playwright/Cypress, TDD
   (1-2 months).

Build a **portfolio of progressively harder projects** to anchor each stage:
e.g. portfolio site → weather/API dashboard → REST API with auth → full MERN/
Django CRUD app → an end-to-end app with payments, real-time, and CI/CD. Document
the *why* and the trade-offs, not just the result.

## AI-augmented workflow (2025+)

AI tools are now part of the stack. Use them to go faster **without** outsourcing
judgment.

**Use AI for**

- Scaffolding (components, routes, models, config), boilerplate, and repetitive
  refactors.
- Drafting tests, fixtures, and documentation.
- Explaining unfamiliar code/errors, exploring options, rubber-ducking design.
- Code review assistance — a second pass, not the only pass.

**Never let AI**

- Ship code you have not read and understood line by line.
- Be the final authority on security, auth, money, or data-loss-adjacent logic —
  verify those yourself.
- Invent APIs/contracts — confirm against real docs (it hallucinates confidently).
- Replace fundamentals — you must be able to debug what it generated.

**Operating rule:** treat AI output as a fast, confident junior's first draft.
Own the result. The bar for what *ships* is unchanged; only the speed of getting
to a reviewable draft changed. The differentiator is increasingly the human
skills AI doesn't replace: system design, judgment under ambiguity, security
instinct, and clear communication.

## Sources distilled into this skill

- Full Stack Developer Roadmap — <https://roadmap.sh/full-stack>
- MERN Full-Stack Roadmap (2025) — <https://dev.to/ayushdevxai/full-stack-development-roadmap-with-ai-2025-4e74>
- Python Web Development with Django (GeeksforGeeks) — <https://www.geeksforgeeks.org/python/python-web-development-django/>
- Full Stack Python — Django — <https://www.fullstackpython.com/django.html>
- React + Django Full-Stack course (Udemy) — <https://www.udemy.com/course/react-django-full-stack/>
- Full Stack Skills catalog (460+ agent skills) — <https://github.com/partme-ai/full-stack-skills/>
- Fullstack-AI Course notes — <https://haruiz.github.io/fullstack-ai-notes/>
