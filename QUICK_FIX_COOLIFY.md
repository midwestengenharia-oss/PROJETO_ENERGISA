# ⚡ CORREÇÃO RÁPIDA - 5 Passos

## 📍 Você está aqui porque:
```
❌ Erro: ERR_CERT_AUTHORITY_INVALID
❌ HTTPS não funciona
```

---

## ✅ SOLUÇÃO EM 5 PASSOS

### 1️⃣ Regenerar Certificado SSL (2 minutos)

**No Coolify:**
```
1. Clique no serviço "frontend"
2. Vá em "Domains"
3. Clique em "Delete Certificate" (se tiver)
4. Clique em "Generate Let's Encrypt Certificate"
5. Aguarde aparecer "Certificate: Valid ✅"
```

---

### 2️⃣ Verificar Configuração dos Serviços

**Frontend:**
- ✅ Domínio: `app.midwestengenharia.com.br`
- ✅ Porta: 80
- ✅ SSL: SIM

**Gateway:**
- ✅ Domínio: ❌ VAZIO (interno)
- ✅ Porta: 3000
- ✅ SSL: NÃO

**Gestor:**
- ✅ Domínio: ❌ VAZIO (interno)
- ✅ Porta: 8000
- ✅ SSL: NÃO

---

### 3️⃣ Atualizar Variáveis de Ambiente

**No serviço Gateway, adicione/edite:**
```env
ALLOWED_ORIGINS=https://app.midwestengenharia.com.br,http://frontend,http://frontend:80
```

**No serviço Frontend (Build Args ou Environment):**
```env
VITE_API_URL=/api
VITE_GATEWAY_URL=/gateway
```

---

### 4️⃣ Rebuild do Frontend

**No Coolify:**
```
1. Vá no serviço "frontend"
2. Clique em "Redeploy" ou "Rebuild"
3. Aguarde completar
```

---

### 5️⃣ Limpar Cache e Testar

**No navegador:**
```
1. Pressione F12 (abrir DevTools)
2. Clique com botão direito no ícone de reload
3. Escolha "Empty Cache and Hard Reload"
4. OU pressione Ctrl+Shift+R
```

**Teste:**
```
Acesse: https://app.midwestengenharia.com.br
Tente fazer login ou simulação
✅ Não deve ter mais erro SSL
```

---

## 🐛 Se AINDA não funcionar:

### Opção A: Verificar DNS
```bash
nslookup app.midwestengenharia.com.br

# Deve retornar o IP do servidor Coolify
```

Se o IP estiver errado, corrija no provedor de DNS.

### Opção B: Verificar Portas
```bash
# No servidor Coolify
sudo ufw status

# Deve mostrar:
# 80/tcp    ALLOW
# 443/tcp   ALLOW
```

### Opção C: Verificar Rede Docker
```bash
# SSH no servidor
docker inspect frontend | grep NetworkMode
docker inspect gateway | grep NetworkMode
docker inspect gestor | grep NetworkMode

# Devem estar na MESMA rede
```

Se não estiverem, no Coolify:
1. Crie rede "energisa"
2. Conecte os 3 serviços nessa rede
3. Reinicie os containers

---

## 📞 Teste Final

```bash
# Teste 1: SSL funciona
curl -I https://app.midwestengenharia.com.br
# Deve retornar: HTTP/2 200

# Teste 2: Proxy funciona
curl https://app.midwestengenharia.com.br/gateway/public/simulacao/iniciar \
  -X POST -H "Content-Type: application/json" -d '{"cpf":"00000000000"}'
# Deve retornar JSON (não erro)
```

---

## ✅ Checklist Final

- [ ] Certificado SSL gerado (frontend)
- [ ] Gateway sem domínio (interno)
- [ ] Gestor sem domínio (interno)
- [ ] ALLOWED_ORIGINS do gateway atualizado
- [ ] Frontend rebuilded
- [ ] Cache do navegador limpo
- [ ] Testado e funcionando

---

## 📚 Documentação Completa

Para mais detalhes, veja:
- `COOLIFY_INTERNAL_SERVICES.md` - Setup detalhado
- `SECURITY.md` - Camadas de segurança
- `RESUMO_SOLUCAO.md` - Explicação técnica completa

---

**⏱️ Tempo estimado:** 10-15 minutos
**🎯 Resultado:** Sistema 100% funcional com SSL válido

🚀 **Boa sorte!**
