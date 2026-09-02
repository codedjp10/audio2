# Aliança Store — Sistema de Gestão de Equipamentos da Igreja

Sistema web para controlar equipamentos, instrumentos, ferramentas, cabos,
conectores, acessórios, materiais de estoque e eventos da igreja — com
histórico completo e permanente de tudo que acontece com cada item.

- **Backend:** Python + Flask
- **Banco de dados:** SQLite (pronto para migrar para PostgreSQL sem mudar o código)
- **Frontend:** HTML + CSS + JavaScript puro (responsivo: menu lateral no PC, navegação inferior no celular)

---

## 1. Arquitetura e estrutura de pastas

```
igreja-sistema/
├── app/
│   ├── __init__.py          # Application factory, registra blueprints
│   ├── config.py            # Configurações (lidas do .env)
│   ├── extensions.py        # SQLAlchemy, Flask-Login, Flask-Migrate
│   ├── models/               # Um arquivo por tabela do banco
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── location.py
│   │   ├── equipment.py      # Itens individuais
│   │   ├── stock.py          # Itens de estoque (quantidade)
│   │   ├── event.py          # Eventos + vínculo com itens
│   │   ├── movement.py       # Histórico de movimentação de equipamentos
│   │   ├── stock_movement.py # Histórico de entradas/saídas de estoque
│   │   └── audit.py          # Log de auditoria
│   ├── routes/                # Um blueprint por área do sistema
│   │   ├── auth.py, dashboard.py, equipment.py, stock.py,
│   │   ├── events.py, users.py, categories.py, locations.py, search.py
│   ├── templates/             # HTML (Jinja2), organizado por área
│   ├── static/
│   │   ├── css/style.css
│   │   ├── js/main.js
│   │   └── uploads/           # Fotos enviadas pelos usuários
│   └── utils/
│       ├── decorators.py      # @admin_required
│       └── helpers.py         # Upload de fotos, log de auditoria
├── instance/                  # Onde o arquivo igreja.db é criado (git-ignored)
├── create_admin.py            # Script de inicialização e criação do 1º admin
├── run.py                     # Ponto de entrada da aplicação
├── requirements.txt
├── .env.example                # Copie para .env e ajuste
└── .gitignore
```

### Modelo de dados e relacionamentos

- **users** — contas de acesso (admin / member)
- **categories** — personalizáveis pelo administrador (`kind`: equipment / stock / both)
- **locations** — locais físicos da igreja
- **equipment** — itens INDIVIDUAIS (equipamentos, instrumentos, ferramentas, cabos completos). Guarda local/status *atuais*; todo histórico fica em `movements`.
- **stock_items** — itens de ESTOQUE (materiais, conectores avulsos). Guarda a quantidade *atual*; todo histórico fica em `stock_movements`.
- **events** — eventos da igreja
- **event_items** — vincula um `equipment` OU um `stock_item` a um `event`
- **movements** — histórico permanente de retiradas/devoluções de equipamentos (nunca apagado)
- **stock_movements** — histórico permanente de entradas/saídas de estoque (nunca apagado)
- **audit_logs** — registro de ações importantes (quem fez o quê e quando)

**Regra de ouro do sistema:** os campos "local atual" e "quantidade atual" são
atualizados a cada operação para consulta rápida, mas cada mudança gera uma
nova linha em `movements` / `stock_movements` que nunca é apagada nem
sobrescrita — é assim que o histórico completo é preservado para sempre.

### Fluxo das principais funções

- **Retirar equipamento:** cria uma linha em `movements` (de → para) e atualiza `equipment.location_id` / `status`.
- **Devolver equipamento:** fecha a movimentação em aberto (`returned_at`) e atualiza `equipment.location_id` / `status` de volta.
- **Entrada/saída de estoque:** cria uma linha em `stock_movements` com saldo anterior e novo, e atualiza `stock_items.quantity` (nunca permite ficar negativo).
- **Eventos:** podem ter equipamentos e materiais vinculados via `event_items`, além de aparecerem como `event_id` nas próprias movimentações/saídas.

---

## 2. Como rodar o sistema no seu computador

### Passo 1 — Instalar o Python

Baixe e instale o Python 3.11+ em https://www.python.org/downloads/
(no Windows, marque a opção "Add Python to PATH" durante a instalação).

### Passo 2 — Criar o ambiente virtual

Abra um terminal dentro da pasta do projeto (`igreja-sistema`) e rode:

```bash
python3 -m venv venv
```

Ative o ambiente virtual:

- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

### Passo 3 — Instalar as dependências

```bash
pip install -r requirements.txt
```

### Passo 4 — Configurar o banco de dados

Copie o arquivo de exemplo de variáveis de ambiente:

```bash
cp .env.example .env
```

(no Windows: `copy .env.example .env`)

Abra o `.env` e troque `SECRET_KEY` por um valor aleatório qualquer (isso
protege as sessões de login). Não é necessário mudar mais nada para rodar
localmente com SQLite.

### Passo 5 — Criar o banco e o primeiro usuário administrador

```bash
python create_admin.py
```

Esse script vai:
1. Criar o arquivo do banco de dados e todas as tabelas.
2. Popular categorias e locais padrão (você pode editar/adicionar depois pelo próprio sistema).
3. Perguntar seu nome, e-mail e senha para criar o usuário Administrador.

### Passo 6 — Executar o sistema

```bash
python run.py
```

### Passo 7 — Acessar pelo navegador

Abra `http://127.0.0.1:5000` no computador que está rodando o sistema.

Para acessar de outros aparelhos na mesma rede Wi-Fi (ex.: celular durante um
evento), descubra o IP local do computador (`ipconfig` no Windows ou
`ifconfig`/`ip a` no Mac/Linux, algo como `192.168.0.x`) e acesse
`http://192.168.0.x:5000` pelo celular.

---

## 3. Preparando para hospedagem futura na internet

O projeto já foi construído pensando nisso:

- Toda a persistência é feita via SQLAlchemy ORM — para trocar de SQLite para
  PostgreSQL, basta alterar a variável `DATABASE_URL` no `.env` (ex.:
  `postgresql://usuario:senha@host:5432/banco`) e instalar o driver
  `psycopg2-binary`. Nenhum código precisa mudar.
- Rode `python create_admin.py` novamente apontando para o novo banco, para
  criar as tabelas e o primeiro administrador nele.
- Para produção, use um servidor WSGI real em vez do servidor de
  desenvolvimento do Flask — o `gunicorn` já está no `requirements.txt`:
  ```bash
  gunicorn -w 4 -b 0.0.0.0:8000 run:app
  ```
- Configure `FLASK_ENV=production` no `.env` do servidor.
- Use um serviço de hospedagem (Render, Railway, PythonAnywhere, um VPS, etc.)
  e configure lá as mesmas variáveis do `.env` (nunca suba o `.env` real para
  um repositório público — ele já está no `.gitignore`).

---

## 4. Uso do dia a dia

- **Administrador** pode cadastrar/editar/excluir equipamentos, itens de
  estoque, categorias, locais, eventos e usuários.
- **Membro da equipe** pode visualizar, pesquisar, registrar retiradas,
  devoluções, entradas e saídas de estoque.
- Toda ação importante fica registrada no log de auditoria (não exibido em
  tela por padrão, mas consultável no banco de dados) e vinculada ao usuário
  logado.
- QR Code não foi implementado propositalmente, mas a estrutura (nomes,
  IDs únicos, categorias) já está pronta para isso ser adicionado no futuro
  sem precisar redesenhar o banco.

Qualquer dúvida durante a instalação, é só chamar.
