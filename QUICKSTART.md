# WordPress Agent - Quick Start ⚡

## 🎯 Co masz gotowe:

✅ Kompletny Python backend (FastAPI)
✅ WordPress REST API client
✅ Claude AI integration dla planowania operacji
✅ Task queue processor (Supabase)
✅ Telegram notifications
✅ Dockerfile dla Coolify
✅ Tabela `wp_agent_tasks` w Supabase utworzona
✅ GitHub push script

## 🚀 Deployment w 3 krokach:

### KROK 1: WordPress Application Password

1. Zaloguj się: https://www.sklep.linguachess.com/wp-admin
2. Users → Your Profile → Application Passwords
3. Dodaj "WordPress Agent" → **SKOPIUJ HASŁO**
4. Zapisz gdzieś bezpiecznie

### KROK 2: Deploy do GitHub + Coolify

```bash
cd /mnt/user-data/outputs/wordpress-agent
chmod +x deploy.sh
./deploy.sh
```

**To zrobi:**
- Push do GitHub: `github.com/szachmacik/wordpress-agent`
- Utworzy app w Coolify
- Ustawi podstawowe env vars

### KROK 3: Uzupełnij secrets w Coolify

Otwórz: https://coolify.ofshore.dev → wordpress-agent → Environment Variables

**Ustaw te 3:**
```
WP_PASSWORD=<Application Password z kroku 1>
SUPABASE_ANON_KEY=<pobierz z Vault>
ANTHROPIC_API_KEY=<Twój Claude API key>
```

Kliknij **Deploy**!

## ✅ TEST - Wyślij pierwsze zadanie

**Opcja A - SQL (Supabase SQL Editor):**
```sql
INSERT INTO wp_agent_tasks (description)
VALUES ('Pokaż wszystkie posty z mojego bloga');
```

**Opcja B - HTTP:**
```bash
curl -X POST https://wp-agent.ofshore.dev/task?task_description="Lista postów"
```

**Sprawdź logi:**
- Coolify → wordpress-agent → Logs
- Telegram - dostaniesz powiadomienie!

## 🎨 Jak używać

### Wysyłaj zadania do kolejki:

```sql
-- Proste zadanie
INSERT INTO wp_agent_tasks (description)
VALUES ('Lista wszystkich kategorii');

-- Utworzenie posta
INSERT INTO wp_agent_tasks (description)
VALUES ('Utwórz nowy draft posta o szachach z tytułem "Otwarcie królewskie" i krótką treścią');

-- Edycja
INSERT INTO wp_agent_tasks (description)
VALUES ('Edytuj post 123 - zmień status na published');

-- Bulk operation
INSERT INTO wp_agent_tasks (description)
VALUES ('Zmień status wszystkich draftów na "do recenzji"');
```

### Agent działa tak:

1. ⏰ Co 10s sprawdza kolejkę (`wp_agent_tasks` gdzie status='pending')
2. 🧠 Wysyła zadanie do Claude API - planowanie operacji
3. ⚙️ Wykonuje operacje na WordPress REST API
4. 📱 Wysyła powiadomienie przez Telegram
5. ✅ Zapisuje wyniki w Supabase

**Wszystko autonomicznie - zero Twojej interwencji!**

## 📊 Monitoring

**Health check:**
```bash
curl https://wp-agent.ofshore.dev/health
```

**Stats:**
```bash
curl https://wp-agent.ofshore.dev/stats
```

**Logi:**
- Real-time w Coolify
- Telegram notifications

## 🔧 Troubleshooting

**Agent nie działa:**
1. Sprawdź logi w Coolify
2. Sprawdź czy env vars są ustawione
3. Test WordPress API: https://www.sklep.linguachess.com/wp-json/wp/v2/posts

**Zadania nie są wykonywane:**
1. Sprawdź czy tabela `wp_agent_tasks` istnieje
2. Sprawdź czy SUPABASE_ANON_KEY jest poprawny
3. Sprawdź logi - agent loguje wszystko

**WordPress errors:**
1. Sprawdź Application Password
2. Sprawdź uprawnienia użytkownika (musi być admin)
3. Sprawdź czy REST API jest włączone

## 💡 Przykłady zadań

```sql
-- Lista postów
INSERT INTO wp_agent_tasks (description) VALUES 
('Pokaż wszystkie posty z ostatniego tygodnia');

-- Utworzenie contentu
INSERT INTO wp_agent_tasks (description) VALUES 
('Utwórz 3 drafty postów o różnych taktykach szachowych: Widelec, Szpila, Przebicie');

-- Edycja
INSERT INTO wp_agent_tasks (description) VALUES 
('Znajdź post o tytule "Test" i zmień jego status na published');

-- Bulk operations
INSERT INTO wp_agent_tasks (description) VALUES 
('Dodaj kategorię "Szachy" do wszystkich postów które jej nie mają');

-- Stats
INSERT INTO wp_agent_tasks (description) VALUES 
('Pokaż statystyki: ile mam postów, stron, kategorii i mediów');
```

## 🎯 Co dalej?

1. **Integracja z Commander Bot:**
   - Dodaj komendy `/wp` do Telegram bota
   - Bot tworzy zadania w `wp_agent_tasks`
   - Dostajesz powiadomienia o wykonaniu

2. **MESH Integration:**
   - Podepnij pod `mesh_task_queue`
   - Synchronizacja z innymi agentami

3. **Scheduled Tasks:**
   - pg_cron do cyklicznych zadań
   - Np. codziennie o 9:00 pokaż statystyki

4. **Advanced Features:**
   - WooCommerce support
   - Media upload
   - Bulk editing
   - Analytics

---

**Agent działa 24/7 - wysyłasz zadanie, zapominasz, dostajesz powiadomienie! 🚀**
