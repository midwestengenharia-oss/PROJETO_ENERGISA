# 🔒 Segurança do Sistema Energisa

## Implementações de Segurança

Este documento descreve todas as camadas de segurança implementadas no sistema para proteger contra ataques e uso indevido.

---

## 🛡️ Camadas de Proteção Implementadas

### 1. **Rate Limiting (Limitação de Taxa)**

**O que protege:** Previne ataques de força bruta e abuso de endpoints

**Como funciona:**
- Limita requisições por IP para cada endpoint
- Configuração padrão: 20 requisições por minuto para rotas públicas
- IPs que excedem o limite recebem erro 429 (Too Many Requests)

**Exemplo:**
```
Endpoint: /public/simulacao/iniciar
Limite: 20 requisições/minuto por IP
Janela de tempo: 60 segundos
```

### 2. **Validação de Sessão com IP Binding**

**O que protege:** Previne Session Hijacking (roubo de sessão)

**Como funciona:**
- Cada sessão é vinculada ao IP do cliente que a criou
- Se alguém tentar usar uma sessão de outro IP, a sessão é invalidada
- O IP suspeito é bloqueado automaticamente

**Exemplo de Ataque Bloqueado:**
```
1. Usuário legítimo cria sessão do IP 192.168.1.10
2. Atacante intercepta o session_id
3. Atacante tenta usar do IP 203.0.113.50
4. Sistema detecta IP diferente → BLOQUEIA o atacante
5. Sessão original é invalidada para proteger o usuário
```

### 3. **Sessões Seguras e Temporárias**

**O que protege:** Previne reutilização de sessões antigas

**Como funciona:**
- Session IDs são hashes criptográficos (SHA-256)
- Expiração automática após 30 minutos
- Limpeza automática de sessões expiradas

**Formato do Session ID:**
```
Antigo: transaction_id previsível da Energisa
Novo: hash SHA-256 único vinculado ao IP + CPF + timestamp
Exemplo: a7f3c9d8e2b1f4a5c6d7e8f9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0
```

### 4. **Headers de Segurança HTTP**

**O que protege:** Previne XSS, Clickjacking, MIME Sniffing

**Headers adicionados automaticamente:**
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
```

### 5. **CORS Restritivo**

**O que protege:** Previne requisições de origens não autorizadas

**Configuração:**
- Origens permitidas controladas por variável de ambiente
- Não aceita wildcard (*) em produção
- Apenas métodos HTTP específicos permitidos

**Como configurar:**
```bash
# No arquivo gateway/.env
ALLOWED_ORIGINS=https://seudominio.com,https://www.seudominio.com
```

### 6. **Detecção de User-Agents Suspeitos**

**O que protege:** Bloqueia bots, scanners e ferramentas de hacking

**User-Agents bloqueados:**
- Bots e crawlers
- Ferramentas de pentesting (Burp, SQLMap, Nikto, etc)
- Scripts automatizados (curl, wget sem customização)
- Requisições sem User-Agent

### 7. **Logging de Auditoria**

**O que protege:** Permite investigação forense após incidentes

**O que é registrado:**
```
[AUDIT] POST /public/simulacao/iniciar | IP: 192.168.1.10 | Status: 200 | UA: Mozilla/5.0...
```

**Eventos importantes:**
- Todas as requisições em rotas públicas
- Tentativas de autenticação falhadas
- IPs bloqueados
- Tentativas de session hijacking

### 8. **Bloqueio Automático de IPs**

**O que protege:** Remove automaticamente atacantes persistentes

**Quando um IP é bloqueado:**
- 5 tentativas de autenticação falhadas em 15 minutos
- Tentativa de session hijacking
- Uso de ferramentas de hacking
- Bloqueio manual via API

**Verificação:**
```python
# IP bloqueado recebe sempre:
HTTP 403 Forbidden
{"detail": "Acesso bloqueado"}
```

### 9. **Proteção contra Replay Attacks**

**O que protege:** Previne reutilização de tokens/sessões capturadas

**Como funciona:**
- Sessions expiram após 30 minutos
- Contador de requisições por sessão
- Sessões invalidadas após uso suspeito

---

## 📋 Configuração para Produção (Coolify)

### Passo 1: Configure as Variáveis de Ambiente

No Coolify, adicione estas variáveis de ambiente no serviço `gateway`:

```bash
# Origens permitidas (seu domínio real)
ALLOWED_ORIGINS=https://seudominio.com.br,https://www.seudominio.com.br

# Chaves secretas (mantenha as existentes)
API_SECRET_KEY="sua_chave_secreta_aqui"
CRM_SECRET="sua_secret_aqui"
```

### Passo 2: Configure SSL/TLS no Coolify

- Certifique-se de que o Coolify está usando HTTPS
- Ative redirecionamento automático HTTP → HTTPS
- Headers de segurança já estão configurados no código

### Passo 3: Monitore os Logs

```bash
# Via Coolify UI ou:
docker logs energisa_gateway --tail 100 -f
```

Procure por:
- `⚠️ ALERTA DE SEGURANÇA`: Tentativas de ataque
- `Rate limit exceeded`: Abuso detectado
- `IP ... bloqueado`: IPs banidos

---

## 🚨 Monitoramento de Segurança

### Logs Importantes

**Tentativa de Session Hijacking:**
```
⚠️ ALERTA DE SEGURANÇA: Tentativa de session hijacking!
Session do IP 192.168.1.10 usada por 203.0.113.50
IP 203.0.113.50 bloqueado. Razão: Tentativa de session hijacking
```

**Rate Limit Excedido:**
```
Rate limit exceeded for IP 203.0.113.50 on endpoint /public/simulacao/iniciar
```

**Falha de Autenticação:**
```
Falha de autenticação do IP 203.0.113.50
IP 203.0.113.50 bloqueado. Razão: Excesso de tentativas de autenticação (5 em 15 min)
```

### Dashboard de Métricas (Futuro)

Para implementar no futuro:
- Grafana + Prometheus para métricas em tempo real
- Alertas automáticos via Telegram/Email
- Dashboard com:
  - IPs bloqueados
  - Taxa de requisições
  - Tentativas de ataque
  - Sessões ativas

---

## 🔧 Administração

### Desbloquear um IP Manualmente

Se você ou um cliente legítimo foi bloqueado por engano, precisará adicionar uma rota administrativa.

**TODO:** Implementar endpoint administrativo:
```python
@app.post("/admin/unblock-ip", dependencies=[Depends(verify_admin_token)])
def unblock_ip(ip: str):
    security_manager.unblock_ip(ip)
    return {"message": f"IP {ip} desbloqueado"}
```

### Listar IPs Bloqueados

**TODO:** Implementar endpoint:
```python
@app.get("/admin/blocked-ips", dependencies=[Depends(verify_admin_token)])
def list_blocked_ips():
    return {"blocked_ips": list(security_manager.blocked_ips)}
```

---

## ⚠️ Ataques Prevenidos

| Tipo de Ataque | Como é Prevenido |
|----------------|------------------|
| **Session Hijacking** | IP binding + validação em cada requisição |
| **Brute Force** | Rate limiting + bloqueio após 5 tentativas |
| **CSRF** | Validação de origem + headers específicos |
| **XSS** | Headers de segurança + CSP |
| **Clickjacking** | X-Frame-Options: DENY |
| **MIME Sniffing** | X-Content-Type-Options: nosniff |
| **Bot Scanning** | Detecção de User-Agent + bloqueio |
| **Replay Attack** | Expiração de sessões + timestamps |
| **DoS/DDoS** | Rate limiting por IP |

---

## 📊 Comparação: Antes vs Depois

| Aspecto | Antes ❌ | Depois ✅ |
|---------|---------|----------|
| **CORS** | `allow_origins=["*"]` aceita qualquer origem | Apenas origens configuradas |
| **Session ID** | Previsível, sem expiração | Hash SHA-256 + expira em 30min |
| **Session Hijacking** | Vulnerável | IP binding impede |
| **Rate Limiting** | Nenhum | 20 req/min por IP |
| **Logging** | Básico | Auditoria completa |
| **Headers de Segurança** | Nenhum | 5 headers críticos |
| **Bloqueio de IPs** | Manual | Automático + heurísticas |

---

## 🎯 Próximos Passos Recomendados

1. **Implementar Captcha** (Google reCAPTCHA v3) no frontend
2. **WAF (Web Application Firewall)** no Coolify/Cloudflare
3. **Autenticação de 2 Fatores** para usuários do gestor
4. **Criptografia de dados sensíveis** no banco de dados
5. **Backup automático** do banco SQLite
6. **Alertas em tempo real** via Telegram/Discord
7. **Penetration Testing** com ferramentas profissionais

---

## 📚 Referências

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [Mozilla Web Security Guidelines](https://infosec.mozilla.org/guidelines/web_security)

---

## 📞 Suporte

Se detectar alguma atividade suspeita ou tiver dúvidas sobre segurança, consulte os logs do gateway:

```bash
docker logs energisa_gateway --tail 500 | grep "ALERTA\|bloqueado\|Rate limit"
```

**Última atualização:** 2025-11-28
**Versão do Sistema:** 2.1.0 (Segurança Hardened)
