import httpx
import re
import asyncio
import time
import os

# --- КОНФИГУРАЦИЯ ---
# GitHub Actions автоматически подставит токен, если мы его укажем в настройках
GITHUB_TOKEN = os.getenv("GH_TOKEN")
OUTPUT_FILE = "all_proxies_list.txt"

# Паттерн для поиска: tg://, t.me/ и telegram.me/
PROXY_PATTERN = r"(?:tg://proxy|https?://(?:t\.me|telegram\.me)/proxy)\?server=([a-zA-Z0-9.-]+)&port=(\d+)&secret=([a-zA-Z0-9]+)"

async def discover_github_sources():
    print("[*] Поиск источников на GitHub...")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    # Поиск по ключевым словам
    query = "t.me/proxy server port secret"
    search_url = f"https://api.github.com/search/code?q={query}&sort=indexed"
    
    # Стартовые проверенные репозитории
    raw_urls = {
        "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
        "https://raw.githubusercontent.com/TelegramProxy/Proxy-List/main/MTProto.txt",
        "https://raw.githubusercontent.com/Therealwh/MTPproxyLIST/main/verified/proxy_all_tme_verified.txt",
        "https://raw.githubusercontent.com/Telegram-FZ-LLC/Telegram-Proxy/main/proxies.txt"
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(search_url, headers=headers)
            if resp.status_code == 200:
                items = resp.json().get('items', [])
                for item in items:
                    raw_url = item['html_url'].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                    raw_urls.add(raw_url)
            else:
                print(f"[!] GitHub API недоступен (код {resp.status_code})")
    except Exception as e:
        print(f"[!] Ошибка поиска: {e}")
    
    return list(raw_urls)

async def parse_proxies():
    unique_proxies = set()
    sources = await discover_github_sources()
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        for url in sources:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    matches = re.findall(PROXY_PATTERN, resp.text)
                    for srv, port, sec in matches:
                        normalized = f"tg://proxy?server={srv}&port={port}&secret={sec}"
                        unique_proxies.add(normalized)
            except:
                continue
    return unique_proxies

async def run_once():
    print(f"[*] Старт сбора: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    proxies = await parse_proxies()
    
    if proxies:
        sorted_proxies = sorted(list(proxies))
        with open(OUTPUT_FILE, "w") as f:
            for p in sorted_proxies:
                f.write(f"{p}\n")
        print(f"[УСПЕХ] Собрано уникальных прокси: {len(proxies)}")
    else:
        print("[!] Прокси не найдены.")

if __name__ == "__main__":
    asyncio.run(run_once())
