# Backend Playbook

Reference for the API/server layer. Covers REST design, the two default stacks
(Node/Express and Python/Django), auth, and security. For deep package/transport
structure, defer to the `backend-architect` skill.

## REST API design

Conventional, predictable APIs reduce the cost of every future integration.

- **Resources are nouns; HTTP verbs are the actions.**
  `GET /users`, `GET /users/{id}`, `POST /users`, `PUT/PATCH /users/{id}`,
  `DELETE /users/{id}`. No verbs in paths (`/getUser` is wrong).
- **Status codes mean something:** 200 OK, 201 Created, 204 No Content,
  400 validation, 401 unauthenticated, 403 unauthorized, 404 not found,
  409 conflict, 422 unprocessable, 429 rate-limited, 500 server error.
- **Consistent error envelope**, e.g. `{ "error": { "code", "message", "details" } }`.
  Never leak stack traces or SQL to clients.
- **Pagination, filtering, sorting** on collection endpoints from day one
  (`?page=&limit=` or cursor-based). Unbounded list endpoints are a future outage.
- **Version** public APIs (`/api/v1`). **Validate every input** server-side.
- Document the contract (OpenAPI/Swagger). The contract is the product boundary.

## Node + Express

```js
// Thin route -> validate -> service -> respond. No business logic in the route.
import { Router } from "express";
import { z } from "zod";

const router = Router();
const createUser = z.object({ email: z.string().email(), name: z.string().min(1) });

router.post("/users", async (req, res, next) => {
  try {
    const input = createUser.parse(req.body);   // validate at the boundary
    const user = await userService.create(input); // business logic in services
    res.status(201).json({ data: user });
  } catch (err) {
    next(err); // centralized error middleware
  }
});

export default router;
```

Rules:

- **Layer it:** routes (HTTP) → services (business logic) → data access. Keep
  business logic out of route handlers.
- One **centralized error-handling middleware**; never let rejections go
  unhandled. Use `async`/`await`, not callback pyramids.
- Apply `helmet`, CORS (allow-list, not `*` for credentialed requests), rate
  limiting, and body-size limits.
- Config via environment (`dotenv` locally, secret manager in prod). Never commit
  `.env`.
- Validate with Zod/Joi at the edge; trust nothing from the client.

## Python + Django

Django is "batteries-included" (ORM, admin, auth, migrations) and follows the
**MVT** pattern: Model (data) → View (request handling) → Template (presentation).

Project shape: a *project* contains *apps*; each app owns one feature
(`users`, `billing`). Register apps in `INSTALLED_APPS`. Use a virtual
environment per project; pin dependencies in `requirements.txt`/`pyproject.toml`.

```python
# models.py — the schema is the source of truth; migrations follow it.
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title
```

```python
# views.py — prefer the ORM; never build SQL by string concatenation.
from django.shortcuts import get_object_or_404, render
from .models import Article

def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    return render(request, "articles/detail.html", {"article": article})
```

Workflow & rules:

- Schema change → `makemigrations` → review the migration → `migrate`. Migrations
  are code: read them before applying, and never edit applied ones.
- **For JSON APIs use Django REST Framework (DRF):** serializers validate I/O,
  viewsets give CRUD, and it handles auth/permissions/throttling.
- Keep views thin; push logic into services/model methods/managers. Fat models /
  thin views.
- Use Django forms / DRF serializers for validation. `{% csrf_token %}` on every
  POST form. Keep `DEBUG = False` and a locked-down `ALLOWED_HOSTS` in production.
- Move secrets and DB credentials to environment/settings, not into `settings.py`
  literals. Swap SQLite → PostgreSQL via the `DATABASES` config for production.

### FastAPI / Flask (when to switch)

- **FastAPI** when you want async-first, type-driven endpoints with automatic
  OpenAPI and Pydantic validation — great for service/microservice APIs.
- **Flask** for a tiny surface where Django is overkill. You will assemble ORM,
  auth, and admin yourself.

## Authentication & authorization

- **Sessions (cookies)** for classic server-rendered/first-party web apps:
  `HttpOnly`, `Secure`, `SameSite`; CSRF protection required.
- **JWT** for stateless APIs / SPAs / mobile: short-lived access token + rotating
  refresh token; store carefully (avoid `localStorage` for sensitive tokens — XSS
  risk). Have a revocation strategy.
- **OAuth2 / OIDC / managed identity** (Auth0, Clerk, Cognito, Google) — prefer
  these over hand-rolled auth unless you have a strong reason.
- **Passwords**: hash with bcrypt/argon2, never store or log plaintext.
- **Authorization ≠ authentication.** Check permissions on every protected
  resource server-side; never rely on the UI hiding a button.

## Security baseline (OWASP Top 10)

- Parameterized queries / ORM only — no string-built SQL (injection).
- Validate and sanitize all input; encode output (XSS).
- CSRF protection on cookie-based auth.
- Rate-limit auth and expensive endpoints; lock-out/backoff on brute force.
- Least-privilege DB credentials; secrets in a manager, never in source/logs.
- Keep dependencies patched (`npm audit`, `pip-audit`); HTTPS everywhere.
- Don't return internal errors/stack traces to clients.

## Real-time

- Use WebSockets (Socket.IO, Django Channels) for push/chat/presence.
- Don't poll when you can subscribe; don't open a socket for request/response
  data that REST handles fine.

## Review checklist

- [ ] Routes/views thin; business logic in a service layer
- [ ] Every input validated server-side; parameterized queries/ORM only
- [ ] Correct status codes + consistent error envelope (no leaked internals)
- [ ] Auth + authorization enforced on every protected resource
- [ ] Secrets via env/secret manager; nothing committed
- [ ] Pagination on list endpoints; no unbounded queries
- [ ] Errors handled centrally; no unhandled async rejections
