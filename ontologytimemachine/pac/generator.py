from typing import List

def _build_domain_matcher(domains: List[str]) -> str:
    """
    Генерує оптимізований JavaScript-код для швидкого пошуку доменів (O(1)).
    Запобігає overhead, якщо список доменів занадто великий.
    """
    js_obj = ",\n    ".join([f'"{d}": true' for d in domains])

    return f"""
var archivoDomains = {{
    {js_obj}
}};

function isOntologyHost(host) {{
    if (!host) return false;
    host = host.toLowerCase();

    // 1. Швидка перевірка на точний збіг по хеш-таблиці
    if (archivoDomains[host]) return true;

    // 2. Оптимізована перевірка піддоменів (наприклад, sub.dbpedia.org -> dbpedia.org)
    var parts = host.split('.');
    while (parts.length > 1) {{
        parts.shift(); // видаляємо ліву частину
        var parentDomain = parts.join('.');
        if (archivoDomains[parentDomain]) return true;
    }}

    return false;
}}
"""


def build_pac(config) -> str:
    """
    Генерує фінальний текст PAC-файлу на основі конфігурації проксі.
    """
    # Обробка хоста: якщо там масив або '0.0.0.0', підставляємо '127.0.0.1' для браузера
    proxy_host = config.host[0] if isinstance(config.host, list) else config.host
    if proxy_host in ["0.0.0.0", "::"]:
        proxy_host = "127.0.0.1"

    proxy = f"PROXY {proxy_host}:{config.port}"

    restricted = getattr(config, "restrictedAccess", True)
    domains = getattr(config, "archivoDomains", ["dbpedia.org", "w3.org"])

    # Якщо увімкнено restricted режим: через проксі йде тільки онтологічний трафік
    if restricted:
        return f"""
{_build_domain_matcher(domains)}

function FindProxyForURL(url, host) {{

    // restricted mode: only ontology traffic goes through proxy
    if (isOntologyHost(host)) {{
        return "{proxy}";
    }}

    return "DIRECT";
}}
""".strip()

    # Звичайний режим: весь трафік загортаємо на проксі
    return f"""
function FindProxyForURL(url, host) {{
    return "{proxy}";
}}
""".strip()