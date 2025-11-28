# 🚀 Deploy Seguro no Coolify - Checklist

## ✅ Checklist de Segurança para Produção

### 1. Variáveis de Ambiente (OBRIGATÓRIO)

No Coolify, configure estas variáveis no serviço **gateway**:

```env
# ⚠️ IMPORTANTE: Substitua pelos seus domínios reais
ALLOWED_ORIGINS=https://seuapp.com.br,https://www.seuapp.com.br

# Mantenha as existentes
API_SECRET_KEY=sua_chave_secreta
CRM_SECRET=sua_secret
```

**Como configurar no Coolify:**
1. Acesse o serviço `gateway`
2. Vá em **Environment Variables**
3. Adicione `ALLOWED_ORIGINS` com seus domínios
4. Clique em **Save**
5. Reinicie o serviço

---

### 2. Configuração de Proxy (Coolify/Traefik)

Certifique-se de que o Coolify está configurado para:

✅ Forçar HTTPS (redirecionar HTTP → HTTPS)
✅ Passar headers `X-Forwarded-For` e `X-Real-IP`
✅ Certificado SSL válido (Let's Encrypt)

**Verificação:**
```bash
curl -I https://seuapp.com.br/public/simulacao/iniciar
```

Deve retornar headers incluindo:
```
Strict-Transport-Security: max-age=31536000
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

---

### 3. Monitoramento de Logs

**Comando para monitorar tentativas de ataque:**
```bash
docker logs energisa_gateway --tail 100 -f | grep -E "ALERTA|bloqueado|Rate limit|suspeito"
```

**O que procurar:**
- `⚠️ ALERTA DE SEGURANÇA` = Tentativa de ataque detectada
- `bloqueado` = IP foi banido automaticamente
- `Rate limit exceeded` = Alguém fazendo muitas requisições

---

### 4. Teste de Segurança Pós-Deploy

Execute estes testes após o deploy:

**Teste 1: CORS**
```bash
# Deve FALHAR (origem não permitida)
curl -H "Origin: https://sitemalicioso.com" \
  https://seuapp.com.br/public/simulacao/iniciar

# Deve FUNCIONAR (origem permitida)
curl -H "Origin: https://seuapp.com.br" \
  https://seuapp.com.br/public/simulacao/iniciar
```

**Teste 2: Rate Limiting**
```bash
# Execute 25 vezes seguidas (vai bloquear após 20)
for i in {1..25}; do
  curl https://seuapp.com.br/public/simulacao/iniciar
done
```

Deve retornar após 20 requisições:
```json
{
  "detail": "Muitas requisições. Tente novamente em alguns segundos."
}
```

**Teste 3: Session Hijacking**
1. Abra o frontend e inicie uma simulação
2. Copie o `session_id` do navegador (DevTools → Network)
3. Tente usar o mesmo `session_id` de outro IP/dispositivo
4. Deve retornar: `{"detail": "Sessão inválida, expirada ou não pertence a este dispositivo"}`

---

### 5. Configuração de Firewall (Opcional mas Recomendado)

Se você tem acesso ao servidor Coolify, configure `ufw`:

```bash
# Permite apenas tráfego do Cloudflare/proxy
ufw allow from <IP_DO_COOLIFY_PROXY>
ufw enable
```

---

### 6. Backup do Banco de Dados

**Configurar backup automático do SQLite:**

```bash
# Criar script de backup
cat > /root/backup_energisa.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/energisa"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)

# Backup do banco SQLite
docker exec energisa_gestor cat /app/gestor_faturas.db > \
  $BACKUP_DIR/gestor_faturas_$DATE.db

# Manter apenas últimos 7 dias
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
EOF

chmod +x /root/backup_energisa.sh

# Adicionar ao cron (diário às 3h da manhã)
(crontab -l 2>/dev/null; echo "0 3 * * * /root/backup_energisa.sh") | crontab -
```

---

### 7. Alertas de Segurança (Via Telegram - Opcional)

**Configurar bot do Telegram para receber alertas:**

1. Crie um bot no Telegram com @BotFather
2. Obtenha o token e chat_id
3. Adicione no gateway/.env:

```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id
```

4. Modifique `security_middleware.py` para enviar alertas críticos

---

### 8. Healthcheck e Uptime Monitoring

**Configure no Coolify:**

1. Vá em **Health Checks** do serviço gateway
2. Endpoint: `/health` (TODO: implementar)
3. Interval: 30s
4. Timeout: 10s

**Ou use serviço externo:**
- [UptimeRobot](https://uptimerobot.com) (grátis)
- [Better Uptime](https://betteruptime.com)
- [Pingdom](https://www.pingdom.com)

---

## 🔐 Checklist Final

Antes de considerar o sistema em produção:

- [ ] Variável `ALLOWED_ORIGINS` configurada com domínios reais
- [ ] HTTPS forçado (sem HTTP)
- [ ] Certificado SSL válido
- [ ] Headers de segurança presentes (testar com curl -I)
- [ ] Rate limiting funcionando (testar 25 requisições)
- [ ] Session hijacking bloqueado (testar com 2 IPs diferentes)
- [ ] Logs de auditoria sendo gerados
- [ ] Backup do banco configurado
- [ ] Monitoramento de uptime ativo
- [ ] Testado fluxo completo de simulação

---

## 🆘 Problemas Comuns

### IP Legítimo Bloqueado

**Sintoma:** Cliente recebe `HTTP 403 Forbidden`

**Causa:** IP foi bloqueado por engano

**Solução Temporária:**
```bash
# Reiniciar o gateway limpa bloqueios em memória
docker-compose restart gateway
```

**Solução Permanente:** Implementar endpoint admin para desbloquear

### CORS Error no Browser

**Sintoma:** `Access to fetch has been blocked by CORS policy`

**Causa:** Domínio não está em `ALLOWED_ORIGINS`

**Solução:**
1. Adicione o domínio completo em `ALLOWED_ORIGINS`
2. Reinicie o gateway
3. Limpe cache do browser (Ctrl+Shift+R)

### Rate Limit Muito Restritivo

**Sintoma:** Usuários legítimos sendo bloqueados

**Solução:** Ajustar em `security_middleware.py`:

```python
# Linha 788
if not security_manager.check_rate_limit(ip, request.url.path, max_requests=50, window_seconds=60):
```

Aumente `max_requests` de 20 para 50.

---

## 📊 Métricas Recomendadas

Monitore estas métricas no Grafana/Cloudflare Analytics:

- **Requisições bloqueadas/dia** (deve ser < 1% do total)
- **IPs únicos bloqueados** (spike indica ataque)
- **Tempo de resposta** (< 500ms no P95)
- **Taxa de erro 4xx/5xx** (< 5%)
- **Sessões ativas** (para dimensionar servidor)

---

## 🎯 Próximo Nível: WAF com Cloudflare

Para proteção adicional (recomendado para produção):

1. Adicione seu domínio ao Cloudflare
2. Ative **WAF** (Web Application Firewall)
3. Configure regras:
   - Bloquear países de alto risco
   - Challenge em tráfego suspeito
   - Rate limiting adicional no edge

**Custo:** Plano grátis do Cloudflare já oferece proteção básica

---

## 📞 Contato em Caso de Incidente

**Se detectar ataque em andamento:**

1. Verifique logs: `docker logs energisa_gateway --tail 500`
2. Identifique IPs atacantes
3. Reinicie gateway se necessário: `docker-compose restart gateway`
4. Considere ativar Cloudflare "Under Attack Mode"

**Logs críticos para análise forense:**
```bash
docker logs energisa_gateway > incident_$(date +%Y%m%d_%H%M%S).log
```

---

**Última atualização:** 2025-11-28
**Versão:** 2.1.0
