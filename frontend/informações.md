Aqui está a documentação técnica completa do projeto **Gestor de Faturas de Energia (SaaS)** que construímos.

Este documento cobre a arquitetura, o banco de dados, os serviços e os fluxos de funcionamento.

-----

# 📘 Documentação do Projeto: Gestor de Faturas SaaS

## 1\. Visão Geral

O sistema é uma plataforma SaaS para gestão centralizada de faturas de energia da Energisa. Ele permite que empresas gerenciem múltiplos CPFs/CNPJs, visualizem faturas, baixem PDFs, copiem códigos PIX/Barras e gerenciem usinas de Geração Distribuída (Solar) com suas beneficiárias.

### 🏗️ Arquitetura de Microserviços

O projeto roda em contêineres **Docker** orquestrados via **Docker Compose**, dividido em 3 serviços principais:

| Serviço | Tecnologia | Porta Interna | Porta Externa | Função |
| :--- | :--- | :--- | :--- | :--- |
| **Gateway** | Python / Playwright | 3000 | 3000 | Interface direta com o site da Energisa (Login, Scraping, Quebra de Captcha). |
| **Gestor** | Python / FastAPI | 8000 | 8000 | "Cérebro" do sistema. Gerencia o Banco de Dados, Regras de Negócio e Sincronização. |
| **Frontend** | React / Vite / Nginx | 80 | 80 | Interface do usuário final (Dashboard). |

-----

## 2\. Banco de Dados (SQLite)

O banco `gestor_faturas.db` (gerenciado pelo SQLAlchemy no serviço **Gestor**) possui a seguinte estrutura relacional:

### Tabela: `clientes`

*Empresas ou pessoas que contratam o SaaS.*

  - `id`: ID único.
  - `nome_empresa`: Nome de exibição.
  - `responsavel_cpf`: CPF usado para login na Energisa.
  - `telefone_login`: Últimos 4 dígitos do telefone (para validação SMS).
  - `status_conexao`: Estado atual (`CONECTADO`, `AGUARDANDO_SMS`, `DESCONECTADO`).

### Tabela: `unidades` (Unidades Consumidoras)

*Imóveis ou Usinas vinculadas ao cliente.*

  - `id`: ID único.
  - `codigo_uc`: Número da UC (Ex: 4160693).
  - `cdc`: Código do Consumidor (Identificador interno da Energisa).
  - `is_geradora` (Bool): Identifica se é uma Usina Solar.
  - `saldo_acumulado`: Saldo de créditos de energia (kWh).
  - `geradora_id` (FK): Auto-relacionamento. Se preenchido, indica que esta UC é "filha" (beneficiária) da UC apontada.
  - `percentual_rateio`: Porcentagem de crédito que recebe da usina pai.

### Tabela: `faturas`

*Histórico financeiro de cada UC.*

  - `id`: ID único.
  - `valor`, `mes`, `ano`, `vencimento`, `status`.
  - `codigo_barras`: Linha digitável do boleto.
  - `pix_copia_cola`: String do QR Code PIX.
  - `consumo_kwh`: Consumo medido no mês.
  - `arquivo_pdf_path`: Caminho local do PDF baixado (Cache).
  - `detalhes_json`: JSON bruto com itens da fatura (impostos, bandeiras, etc).

-----

## 3\. Detalhamento dos Serviços

### 🟢 Serviço 1: Gateway (API de Integração)

**Localização:** `/gateway`
Responsável pela "parte suja" da automação. Usa um navegador *headless* controlado para acessar o portal da Energisa.

  * **Autenticação:** Simula o fluxo de Login com CPF e intercepta o envio de SMS.
  * **Sessão:** Mantém cookies e tokens de sessão (`accessToken`, `rtk`) salvos em arquivos JSON locais para reutilização.
  * **Endpoints Principais:**
      * `/auth/login/start`: Inicia login e pede SMS.
      * `/auth/login/finish`: Recebe código SMS e finaliza sessão.
      * `/ucs`: Lista unidades do CPF logado.
      * `/faturas/listar`: Busca JSON de faturas de uma UC.
      * `/gd/info`: Endpoint especial para dados de Geração Distribuída (Saldo/Beneficiárias).

### 🟠 Serviço 2: Gestor (Backend API)

**Localização:** `/gestor`
A inteligência do negócio. É quem o Frontend chama.

  * **Fluxo de Sincronização (`sincronizar_dados_cliente`):**
    1.  Chama Gateway para listar UCs.
    2.  **Detecta Usinas:** Se o campo `geracaoDistribuida` for igual ao número da UC, marca como `is_geradora=True`.
    3.  **Busca Solar:** Se for usina, chama `/gd/info` para pegar saldo e lista de beneficiárias, criando a árvore "Pai-Filho" no banco.
    4.  **Baixa Faturas:** Itera sobre as UCs principais e baixa o histórico financeiro, salvando PIX e Código de Barras.
    5.  **Tratamento de Erros:** Possui lógica robusta para ignorar falhas em UCs individuais e continuar o processamento das demais.
  * **Lazy Loading:**
      * `/empresas/{id}/ucs`: Retorna apenas a lista de UCs (leve).
      * `/ucs/{id}/faturas`: Retorna as faturas apenas quando o usuário clica para expandir (pesado).
  * **Download Inteligente:**
      * Ao pedir um PDF, verifica se já existe na pasta `faturas_storage`.
      * Se não existir, chama o Gateway, baixa, salva em disco e devolve ao usuário.

### 🔵 Serviço 3: Frontend (Dashboard)

**Localização:** `/frontend`
Interface construída com React, Vite e Tailwind CSS.

  * **Dashboard Geral:** Lista empresas e status de conexão.
  * **Aba "Faturas":**
      * Lista de UCs.
      * **Botão "Ver Faturas":** Carrega faturas sob demanda (Lazy Load).
      * **Botão "Detalhes":** Abre modal com Código de Barras e PIX Copia e Cola.
      * **Botão "PDF":** Botão com estado de *loading* (spinner) durante o download.
  * **Aba "Gestão Usinas":**
      * Visualização hierárquica.
      * Mostra a Usina (Pai) com saldo de créditos.
      * Lista as Beneficiárias (Filhos) com seus percentuais de rateio.

-----

## 4\. Como Rodar o Projeto

### Pré-requisitos

  * Docker e Docker Compose instalados.

### Comandos

1.  **Iniciar o Sistema (Primeira vez ou após alterações):**
    ```bash
    docker-compose up --build
    ```
2.  **Reiniciar apenas o Backend (após mudar código Python):**
    ```bash
    docker-compose restart gestor
    ```
3.  **Resetar Banco de Dados (se mudar estrutura das tabelas):**
    ```bash
    docker-compose down -v
    docker-compose up --build
    ```

### Acesso

  * **Frontend (Painel):** http://localhost
  * **Swagger Backend (Gestor):** http://localhost:8000/docs
  * **Swagger Gateway (Integração):** http://localhost:3000/docs

-----

## 5\. Fluxo de Uso Típico

1.  **Cadastro:** Usuário cria uma empresa no Frontend (Nome, CPF, Telefone).
2.  **Conexão:**
      * Usuário clica em "Conectar Energisa".
      * Gateway abre navegador e pede SMS.
      * Energisa envia SMS para o celular do cliente.
      * Usuário digita o código no Frontend.
3.  **Sincronização (Automática):**
      * Ao validar o SMS, o Gestor dispara o robô em *background*.
      * O robô varre a conta, identifica usinas, cria relacionamentos e baixa faturas.
4.  **Visualização:**
      * Usuário vê status "CONECTADO".
      * Acessa os dados, visualiza saldo solar e baixa boletos.