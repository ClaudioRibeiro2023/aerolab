# Headers de Segurança

> Configuração de headers HTTP de segurança do AeroLab.

**Fonte:** `api-template/app/security.py`, `api-template/app/middleware.py`

---

## Visão Geral

O AeroLab implementa headers de segurança recomendados pela OWASP para proteção contra ataques comuns.

---

## Headers Implementados

### SecurityHeadersMiddleware

**Fonte:** `api-template/app/middleware.py`

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS Protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS (em produção)
        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = \
                "max-age=31536000; includeSubDomains"

        return response
```

---

## Detalhamento dos Headers

### X-Content-Type-Options

```http
X-Content-Type-Options: nosniff
```

**Propósito:** Previne que browsers "adivinhem" o MIME type do conteúdo.

**Proteção contra:** MIME confusion attacks, XSS via upload de arquivos.

### X-Frame-Options

```http
X-Frame-Options: DENY
```

**Propósito:** Impede que a página seja carregada em iframes.

**Proteção contra:** Clickjacking.

**Valores possíveis:**

- `DENY` - Nunca permitir iframe
- `SAMEORIGIN` - Permitir apenas do mesmo domínio
- `ALLOW-FROM uri` - Permitir de URI específica (deprecated)

### X-XSS-Protection

```http
X-XSS-Protection: 1; mode=block
```

**Propósito:** Ativa filtro XSS em browsers antigos.

**Nota:** Browsers modernos removeram este filtro. CSP é a proteção atual.

### Referrer-Policy

```http
Referrer-Policy: strict-origin-when-cross-origin
```

**Propósito:** Controla quanta informação é enviada no header Referer.

**Valores comuns:**

- `no-referrer` - Nunca enviar
- `same-origin` - Apenas para mesmo domínio
- `strict-origin-when-cross-origin` - Origin completa para mesmo domínio, apenas origin para cross-origin

### Strict-Transport-Security (HSTS)

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

**Propósito:** Força browsers a usar HTTPS.

**Parâmetros:**

- `max-age=31536000` - Cache por 1 ano
- `includeSubDomains` - Aplica a todos os subdomínios
- `preload` - Permite inclusão na lista HSTS preload

**⚠️ Ativar apenas em produção com HTTPS configurado.**

---

## Content Security Policy (CSP)

**Fonte:** `api-template/app/security.py`

### Configuração

```python
CSP_POLICY = {
    "default-src": ["'self'"],
    "script-src": ["'self'"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'", "data:", "https:"],
    "font-src": ["'self'"],
    "connect-src": [
        "'self'",
        "http://localhost:8000",
        "http://localhost:8080",
    ],
    "frame-ancestors": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
}
```

### Diretivas Explicadas

| Diretiva          | Valor                    | Descrição                           |
| ----------------- | ------------------------ | ----------------------------------- |
| `default-src`     | `'self'`                 | Fallback para outras diretivas      |
| `script-src`      | `'self'`                 | Apenas scripts do próprio domínio   |
| `style-src`       | `'self' 'unsafe-inline'` | Estilos locais + inline (Tailwind)  |
| `img-src`         | `'self' data: https:`    | Imagens locais, data URIs, HTTPS    |
| `connect-src`     | `'self' + APIs`          | Conexões permitidas (fetch, XHR)    |
| `frame-ancestors` | `'none'`                 | Equivalente a X-Frame-Options: DENY |
| `base-uri`        | `'self'`                 | Restringe <base> tag                |
| `form-action`     | `'self'`                 | Destinos de formulários             |

### Endpoint de Violação

```python
@app.post("/api/csp-report")
async def csp_report(request: Request):
    """Recebe relatórios de violação CSP."""
    report = await request.json()
    logger.warning("csp_violation", report=report)
    return {"status": "received"}
```

Header para reportar violações:

```http
Content-Security-Policy-Report-Only: ...; report-uri /api/csp-report
```

---

## CORS

**Fonte:** `api-template/app/main.py:43-55`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:13000",
        os.getenv("FRONTEND_URL", "http://localhost:13000"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Request-ID",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset"
    ],
)
```

### Produção

Restringir `allow_origins` apenas para domínios autorizados:

```python
allow_origins=[
    "https://app.yourdomain.com",
]
```

---

## CSRF Protection

**Fonte:** `api-template/app/csrf.py`

### Implementação

Pattern: **Double Submit Cookie**

```python
# Gerar token CSRF
csrf_token = generate_csrf_token()
response.set_cookie(
    "csrf_token",
    csrf_token,
    httponly=False,  # JavaScript precisa ler
    samesite="strict",
    secure=True,  # Em produção
)

# Validar em mutações
@app.post("/api/resource")
async def create_resource(
    request: Request,
    csrf_token: str = Header(..., alias="X-CSRF-Token")
):
    cookie_token = request.cookies.get("csrf_token")
    if not verify_csrf(cookie_token, csrf_token):
        raise HTTPException(403, "Invalid CSRF token")
```

### Uso no Frontend

```typescript
// Ler cookie e enviar no header
const csrfToken = document.cookie
  .split('; ')
  .find(row => row.startsWith('csrf_token='))
  ?.split('=')[1]

fetch('/api/resource', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrfToken,
  },
  body: JSON.stringify(data),
})
```

---

## Checklist de Segurança

### Desenvolvimento

- [ ] CORS configurado para localhost apenas
- [ ] CSP em modo report-only para debug
- [ ] HSTS desativado

### Produção

- [ ] CORS restrito a domínios de produção
- [ ] CSP em modo enforce
- [ ] HSTS ativado com includeSubDomains
- [ ] Todos os cookies com Secure flag
- [ ] HTTPS forçado em todo o site

---

## Teste de Headers

### Usando curl

```bash
curl -I http://localhost:8000/health
```

### Usando securityheaders.com

1. Acesse https://securityheaders.com
2. Digite a URL de produção
3. Verifique nota A ou A+

### Headers Esperados

```http
HTTP/1.1 200 OK
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; ...
```

---

**Arquivos relacionados:**

- `api-template/app/security.py`
- `api-template/app/middleware.py`
- `api-template/app/csrf.py`
