# WordPress Agent - Autonomous Service

**Autonomiczny agent WordPress** - działa w tle 24/7, nasłuchuje zadań w Supabase i wykonuje operacje na WordPress bez Twojej interwencji.

## 🎯 Jak to działa?

```
Telegram Commander Bot → Supabase task queue → WordPress Agent → WordPress REST API
                                                       ↓
                                                 Claude API (planning)
                                                       ↓
                                                 Telegram (notifications)
```

## 📋 Setup - KROK PO KROKU

### 1. WordPress - Utwórz Application Password

1. Zaloguj się do WP Admin: https://www.sklep.linguachess.com/wp-admin
2. Users → Your Profile
3. Scroll w dół do **Application Passwords**
4. Dodaj nazwę: `WordPress Agent`
5. Kliknij **Add New**
6. **SKOPIUJ HASŁO** (format: `xxxx xxxx xxxx xxxx xxxx xxxx`)

### 2. Supabase - Utwórz tabelę zadań

```sql
-- Tabela dla zadań WordPress
CREATE TABLE IF NOT EXISTS wp_agent_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  description TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
  created_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  summary TEXT,
  results JSONB,
  error TEXT
);

-- Index dla szybkiego queryowania pending tasks
CREATE INDEX idx_wp_tasks_status ON wp_agent_tasks(status, created_at);

-- RLS (opcjonalnie)
ALTER TABLE wp_agent_tasks ENABLE ROW LEVEL SECURITY;
```

### 3. GitHub - Utwórz repo i push

```bash
cd wordpress-agent
git init
git add .
git commit -m "WordPress Agent - autonomous service"
git remote add origin https://github.com/szachmacik/wordpress-agent.git
git push -u origin main
```

### 4. Coolify - Deploy

**A) Przez UI:**
1. New Resource → Git Repository
2. Repository: `szachmacik/wordpress-agent`
3. Branch: `main`
4. Build Pack: Dockerfile
5. Port: 3000
6. Domain: `wp-agent.ofshore.dev`

**B) Environment Variables w Coolify:**
```
WP_URL=https://www.sklep.linguachess.com
WP_USERNAME=admin
WP_PASSWORD=<Application Password z kroku 1>
SUPABASE_URL=https://blgdhfcosqjzrutncbbr.supabase.co
SUPABASE_ANON_KEY=<z Supabase Vault>
ANTHROPIC_API_KEY=<Twój API key>
TELEGRAM_BOT_TOKEN=8768280651:AAF7PtL_-zvJXffvQngTtgC_rqfPdzzZN0Y
TELEGRAM_CHAT_ID=8149345223
```

**C) Deploy!**

### 5. Test - Wyślij pierwsze zadanie

**Opcja A - SQL (Supabase SQL Editor):**
```sql
INSERT INTO wp_agent_tasks (description)
VALUES ('Pokaż wszystkie posty z ostatniego tygodnia');
```

**Opcja B - HTTP (curl):**
```bash
curl -X POST https://wp-agent.ofshore.dev/task?task_description="Lista wszystkich postów"
```

**Opcja C - Telegram Commander Bot (TODO):**
```
/wp lista wszystkich postów
```

## 🚀 Jak używać - po deployment

### Wysyłanie zadań:

**1. Przez Supabase:**
```sql
INSERT INTO wp_agent_tasks (description)
VALUES ('Utwórz nowy post o szachach z tytułem "Otwarcie królewskie"');
```

**2. Przez HTTP API:**
```bash
curl -X POST https://wp-agent.ofshore.dev/task \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Edytuj post 123 - dodaj więcej szczegółów"}'
```

**3. Przez Telegram (integracja z Commander):**
```
/wp utwórz draft posta o taktykach szachowych
/wp pokaż wszystkie drafty
/wp edytuj post X - dodaj kategorie
```

### Monitoring:

**Health check:**
```bash
curl https://wp-agent.ofshore.dev/health
```

**Stats:**
```bash
curl https://wp-agent.ofshore.dev/stats
```

**Logi w Coolify:**
- Otwórz Coolify → WordPress Agent → Logs

**Powiadomienia:**
- Automatycznie w Telegram przez Commander bota

## 💡 Przykłady zadań

### Podstawowe:
- "Pokaż wszystkie posty z ostatniego tygodnia"
- "Utwórz nowy draft posta z tytułem 'Test'"
- "Lista wszystkich kategorii i tagów"
- "Pokaż wszystkie drafty"

### Zaawansowane:
- "Utwórz 5 draftów postów o różnych taktykach szachowych"
- "Zmień status wszystkich draftów na 'do recenzji'"
- "Edytuj post 123 - dodaj kategorie 'Nauka' i 'Taktyka'"
- "Usuń wszystkie posty starsze niż 6 miesięcy"

## 🔧 Integracja z MESH (opcjonalnie)

Możesz podpiąć WordPress Agent pod MESH system:

```sql
-- Dodaj device
INSERT INTO mesh_devices (device_id, device_type, capabilities, config)
VALUES (
  'wp-agent-01',
  'wordpress_agent',
  '{"can_create_posts": true, "can_edit_posts": true, "can_manage_media": true}',
  '{"wp_url": "https://www.sklep.linguachess.com"}'::jsonb
);

-- Potem wysyłaj zadania do mesh_task_queue
-- WordPress Agent będzie je automatycznie odbierał
```

## 🎨 Architektura

```
┌─────────────────────────────────────────────────────────────┐
│                     WordPress Agent                          │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   FastAPI   │  │ Task         │  │ WordPress    │       │
│  │   Server    │→ │ Processor    │→ │ Client       │───┐   │
│  └─────────────┘  └──────────────┘  └──────────────┘   │   │
│         │                │                              │   │
│         │                ↓                              │   │
│         │         ┌──────────────┐                      │   │
│         │         │ Claude       │                      │   │
│         │         │ Planner      │                      │   │
│         │         └──────────────┘                      │   │
│         │                │                              │   │
│         │                ↓                              │   │
│         │         ┌──────────────┐                      │   │
│         └────────→│ Telegram     │                      │   │
│                   │ Notifier     │                      │   │
│                   └──────────────┘                      │   │
└─────────────────────────────────────────────────────────┼───┘
                                                          │
                    ┌─────────────────────────────────────┘
                    │
                    ↓
           ┌─────────────────┐
           │  WordPress      │
           │  REST API       │
           │  (Zenbox)       │
           └─────────────────┘

External:
  ┌──────────────┐
  │  Supabase    │  wp_agent_tasks table
  │  (Queue)     │  
  └──────────────┘
```

## 📊 Monitoring & Debugging

**Logi:**
- Real-time w Coolify Logs
- Poziomy: INFO, WARNING, ERROR
- Każda operacja logowana

**Metryki:**
```
GET /stats
{
  "tasks_processed": 42,
  "tasks_failed": 2,
  "operations_executed": 156,
  "started_at": "2025-03-25T12:00:00"
}
```

**Health:**
```
GET /health
{
  "status": "healthy",
  "components": {
    "task_processor": true,
    "wordpress": true
  }
}
```

## 🐛 Troubleshooting

**Agent nie odbiera zadań:**
- Sprawdź czy Supabase anon key jest poprawny
- Sprawdź czy tabela `wp_agent_tasks` istnieje
- Sprawdź logi w Coolify

**WordPress connection failed:**
- Sprawdź Application Password
- Sprawdź czy REST API działa: https://www.sklep.linguachess.com/wp-json/wp/v2/posts
- Sprawdź uprawnienia użytkownika (musi być admin)

**Claude planning errors:**
- Sprawdź ANTHROPIC_API_KEY
- Sprawdź logi - Claude może zwrócić błąd w planowaniu

## 🔒 Security

- **Application Password** - bezpieczniejsze niż główne hasło
- **Supabase RLS** - opcjonalnie włącz Row Level Security
- **Secrets w Vault** - przechowuj w Supabase Vault
- **HTTPS** - wszystkie komunikacje szyfrowane

## 📝 TODO / Future Features

- [ ] Telegram Commander integration (`/wp` commands)
- [ ] Scheduled tasks (cron-like)
- [ ] Bulk operations (batch processing)
- [ ] WordPress webhooks (react to WP events)
- [ ] Advanced filtering (by category, tag, author)
- [ ] Media upload support
- [ ] WooCommerce support (products, orders)
- [ ] Analytics & reporting

---

**Agent działa 24/7 - wysyłasz zadanie do kolejki, agent je wykona autonomicznie!** 🚀
