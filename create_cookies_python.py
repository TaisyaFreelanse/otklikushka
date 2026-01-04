import json

cookies = [
  {
    "domain": ".freelancehunt.com",
    "expiry": 1802046603,
    "httpOnly": False,
    "name": "_ga_D5VKDWKRBW",
    "path": "/",
    "sameSite": "Lax",
    "secure": False,
    "value": "GS2.1.s1767486503$o2$g1$t1767486603$j60$l1$h34997339"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1793406523,
    "httpOnly": False,
    "name": "_BEAMER_LAST_PUSH_PROMPT_INTERACTION_jBFAZxmY547",
    "path": "/",
    "sameSite": "None",
    "secure": True,
    "value": "1767486523006"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1799022503,
    "httpOnly": False,
    "name": "_clck",
    "path": "/",
    "sameSite": "Lax",
    "secure": False,
    "value": "1n09rrr%5E2%5Eg2f%5E0%5E2194"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1802046603,
    "httpOnly": False,
    "name": "_ga",
    "path": "/",
    "sameSite": "Lax",
    "secure": False,
    "value": "GA1.1.186277177.1767484044"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1793406608,
    "httpOnly": False,
    "name": "_BEAMER_USER_ID_jBFAZxmY547",
    "path": "/",
    "sameSite": "None",
    "secure": True,
    "value": "e609812a-a2cd-46ba-864f-41b5a8c05c9c"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1799022603,
    "httpOnly": False,
    "name": "cookieyes-consent",
    "path": "/",
    "sameSite": "Strict",
    "secure": True,
    "value": "consentid:Uk1oMUJoa1NmbDM2WXJ0Wms0blpsOHJjU0xzd3ZHclk,consent:yes,action:no,necessary:yes,functional:yes,analytics:yes,performance:yes,advertisement:yes,other:yes"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1767487709,
    "httpOnly": False,
    "name": "user_data.sha256_phone_number",
    "path": "/",
    "sameSite": "Lax",
    "secure": True,
    "value": "b23b91852da1cd3108037e08378702a0230acab7a3f553968e6bdb04d82febd2"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1783036109,
    "httpOnly": False,
    "name": "pid3",
    "path": "/",
    "sameSite": "Lax",
    "secure": True,
    "value": "MEMjn8B%2FsFu9eR7EJzOksQ%3D%3D"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1775262633,
    "httpOnly": False,
    "name": "_fbp",
    "path": "/",
    "sameSite": "Lax",
    "secure": False,
    "value": "fb.1.1767484055928.757324336832713004"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1767487756,
    "httpOnly": False,
    "name": "_BEAMER_FILTER_BY_URL_jBFAZxmY547",
    "path": "/",
    "sameSite": "None",
    "secure": True,
    "value": "false"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1768693709,
    "httpOnly": True,
    "name": "rmt2",
    "path": "/",
    "sameSite": "Lax",
    "secure": True,
    "value": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpbiI6InRhaXNpYWFhMSIsInJlbWVtYmVyX21lX2tleSI6MTc0NzE2NTM5NywiaXNfYXV0aGVudGljYXRlZF9ieV8yZmEiOmZhbHNlLCJleHAiOjE3Njg2OTM3MDd9.-ICJ_mCokuhLMT9cDEomzKyvE3qPOMtnxbBNjwMAd9s"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1767573003,
    "httpOnly": False,
    "name": "_clsk",
    "path": "/",
    "sameSite": "Lax",
    "secure": False,
    "value": "7q8ybq%5E1767486603854%5E4%5E1%5Ez.clarity.ms%2Fcollect"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1793406603,
    "httpOnly": False,
    "name": "_BEAMER_FIRST_VISIT_jBFAZxmY547",
    "path": "/",
    "sameSite": "None",
    "secure": True,
    "value": "2026-01-03T23:48:30.641Z"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1799020045,
    "httpOnly": False,
    "name": "device-referrer",
    "path": "/",
    "sameSite": "Lax",
    "secure": True,
    "value": ""
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1775260044,
    "httpOnly": False,
    "name": "_gcl_au",
    "path": "/",
    "sameSite": "Lax",
    "secure": False,
    "value": "1.1.1288242143.1767484044"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1769903309,
    "httpOnly": True,
    "name": "rmp",
    "path": "/",
    "sameSite": "Lax",
    "secure": True,
    "value": "taisiaaa1"
  },
  {
    "domain": ".freelancehunt.com",
    "httpOnly": True,
    "name": "sid2",
    "path": "/",
    "sameSite": "Lax",
    "secure": True,
    "value": "87148d732a030c6a001f96d1b85a195f5f4a6ee88fe245b3"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1769903309,
    "httpOnly": True,
    "name": "rmfn",
    "path": "/",
    "sameSite": "Lax",
    "secure": True,
    "value": "%D0%A2%D0%B0%D1%96%D1%81%D1%96%D1%8F"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1767487709,
    "httpOnly": False,
    "name": "user_data.sha256_email_address",
    "path": "/",
    "sameSite": "Lax",
    "secure": True,
    "value": "4307b34f18c51b95a0766c260809def6fc18f56c527ba4aef91c034ca53fea14"
  },
  {
    "domain": ".freelancehunt.com",
    "expiry": 1799020045,
    "httpOnly": False,
    "name": "device-source",
    "path": "/",
    "sameSite": "Lax",
    "secure": True,
    "value": "https://freelancehunt.com/ua"
  }
]

import os
os.makedirs('/app/data', exist_ok=True)

with open('/app/data/cookies.json', 'w', encoding='utf-8') as f:
    json.dump(cookies, f, indent=2, ensure_ascii=False)

print("Cookies file created successfully!")
print(f"File size: {os.path.getsize('/app/data/cookies.json')} bytes")

