# 🚀 Быстрая загрузка cookies на Render

## Шаг 1: Откройте Render Shell

1. Перейдите: https://dashboard.render.com/web/srv-d5crfrtactks73csled0
2. Нажмите **"Shell"** в левом меню

## Шаг 2: Загрузите cookies

Скопируйте и выполните ВСЮ эту команду в Render Shell:

```bash
mkdir -p /app/data && cat > /app/data/cookies.json << 'COOKIES_EOF'
[
  {
    "domain": ".freelancehunt.com",
    "expiry": 1802046603,
    "httpOnly": false,
    "name": "_ga_D5VKDWKRBW",
    "path": "/",
    "sameSite": "Lax",
    "secure": false,
    "value": "GS2.1.s1767486503$o2$g1$t1767486603$j60$l1$h34997339"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1793406523,
    "httpOnly": false,
    "name": "_BEAMER_LAST_PUSH_PROMPT_INTERACTION_jBFAZxmY547",
    "path": "/",
    "sameSite": "None",
    "secure": true,
    "value": "1767486523006"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1799022503,
    "httpOnly": false,
    "name": "_clck",
    "path": "/",
    "sameSite": "Lax",
    "secure": false,
    "value": "1n09rrr%5E2%5Eg2f%5E0%5E2194"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1802046603,
    "httpOnly": false,
    "name": "_ga",
    "path": "/",
    "sameSite": "Lax",
    "secure": false,
    "value": "GA1.1.186277177.1767484044"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1793406608,
    "httpOnly": false,
    "name": "_BEAMER_USER_ID_jBFAZxmY547",
    "path": "/",
    "sameSite": "None",
    "secure": true,
    "value": "e609812a-a2cd-46ba-864f-41b5a8c05c9c"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1799022603,
    "httpOnly": false,
    "name": "cookieyes-consent",
    "path": "/",
    "sameSite": "Strict",
    "secure": true,
    "value": "consentid:Uk1oMUJoa1NmbDM2WXJ0Wms0blpsOHJjU0xzd3ZHclk,consent:yes,action:no,necessary:yes,functional:yes,analytics:yes,performance:yes,advertisement:yes,other:yes"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1767487709,
    "httpOnly": false,
    "name": "user_data.sha256_phone_number",
    "path": "/",
    "sameSite": "Lax",
    "secure": true,
    "value": "b23b91852da1cd3108037e08378702a0230acab7a3f553968e6bdb04d82febd2"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1783036109,
    "httpOnly": false,
    "name": "pid3",
    "path": "/",
    "sameSite": "Lax",
    "secure": true,
    "value": "MEMjn8B%2FsFu9eR7EJzOksQ%3D%3D"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1775262633,
    "httpOnly": false,
    "name": "_fbp",
    "path": "/",
    "sameSite": "Lax",
    "secure": false,
    "value": "fb.1.1767484055928.757324336832713004"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1767487756,
    "httpOnly": false,
    "name": "_BEAMER_FILTER_BY_URL_jBFAZxmY547",
    "path": "/",
    "sameSite": "None",
    "secure": true,
    "value": "false"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1768693709,
    "httpOnly": true,
    "name": "rmt2",
    "path": "/",
    "sameSite": "Lax",
    "secure": true,
    "value": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpbiI6InRhaXNpYWFhMSIsInJlbWVtYmVyX21lX2tleSI6MTc0NzE2NTM5NywiaXNfYXV0aGVudGljYXRlZF9ieV8yZmEiOmZhbHNlLCJleHAiOjE3Njg2OTM3MDd9.-ICJ_mCokuhLMT9cDEomzKyvE3qPOMtnxbBNjwMAd9s"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1767573003,
    "httpOnly": false,
    "name": "_clsk",
    "path": "/",
    "sameSite": "Lax",
    "secure": false,
    "value": "7q8ybq%5E1767486603854%5E4%5E1%5Ez.clarity.ms%2Fcollect"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1793406603,
    "httpOnly": false,
    "name": "_BEAMER_FIRST_VISIT_jBFAZxmY547",
    "path": "/",
    "sameSite": "None",
    "secure": true,
    "value": "2026-01-03T23:48:30.641Z"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1799020045,
    "httpOnly": false,
    "name": "device-referrer",
    "path": "/",
    "sameSite": "Lax",
    "secure": true,
    "value": ""
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1775260044,
    "httpOnly": false,
    "name": "_gcl_au",
    "path": "/",
    "sameSite": "Lax",
    "secure": false,
    "value": "1.1.1288242143.1767484044"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1769903309,
    "httpOnly": true,
    "name": "rmp",
    "path": "/",
    "sameSite": "Lax",
    "secure": true,
    "value": "taisiaaa1"
  },
  {
    "domain": ".freelancehunt.com",
    "httpOnly": true,
    "name": "sid2",
    "path": "/",
    "sameSite": "Lax",
    "secure": true,
    "value": "87148d732a030c6a001f96d1b85a195f5f4a6ee88fe245b3"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1769903309,
    "httpOnly": true,
    "name": "rmfn",
    "path": "/",
    "sameSite": "Lax",
    "secure": true,
    "value": "%D0%A2%D0%B0%D1%96%D1%81%D1%96%D1%8F"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1767487709,
    "httpOnly": false,
    "name": "user_data.sha256_email_address",
    "path": "/",
    "sameSite": "Lax",
    "secure": true,
    "value": "4307b34f18c51b95a0766c260809def6fc18f56c527ba4aef91c034ca53fea14"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1799020045,
    "httpOnly": false,
    "name": "device-source",
    "path": "/",
    "sameSite": "Lax",
    "secure": true,
    "value": "https://freelancehunt.com/ua"
  }
]
COOKIES_EOF
```

## Шаг 3: Проверьте файл

```bash
ls -lh /app/data/cookies.json
cat /app/data/cookies.json | head -3
```

Должно показать файл размером примерно 3-4 KB.

## Шаг 4: Готово!

Cookies загружены. Бот автоматически подхватит их при следующей проверке проектов.

**Проверьте работу:**
- Отправьте `/start` боту в Telegram
- Проверьте логи в Render Dashboard → Logs

---

**Примечание:** Если команда выше не работает, используйте способ через nano (см. UPLOAD_COOKIES_INSTRUCTIONS.md)

