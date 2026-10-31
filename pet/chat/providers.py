from __future__ import annotations
import functools, ssl
import re as _re

try:
    import certifi
except Exception:
    certifi = None

from .models import ProviderError, StreamEvent  # noqa: F401 — 向后兼容重导出


def _make_ssl_context(verify: bool):
    """按配置构造 SSL 上下文：verify=False 跳过证书校验（本地网关/自签名）；
    verify=True 优先使用 certifi 的 CA 包（PyInstaller 需 --collect-all certifi）。

    构造结果按 ``verify`` 缓存：SSLContext 建好后只读复用是安全的，而
    ``create_default_context(cafile=...)`` 每次新建实测要 ~0.5 s（certifi 加载）。
    """
    if not verify:
        return ssl._create_unverified_context()
    return _verified_ssl_context()


@functools.lru_cache(maxsize=1)
def _verified_ssl_context():
    try:
        if certifi is not None:
            return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    return ssl.create_default_context()


def build_browser_headers(extra: dict | None = None) -> dict[str, str]:
    """构造带浏览器特征的请求头，降低 Cloudflare 等 WAF 的机器人误判。"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }
    if extra:
        headers.update(extra)
    return headers


def normalize_chat_endpoint(base_url, chat_path='/v1/chat/completions'):
    base = str(base_url or '').strip().rstrip('/')
    path = str(chat_path or '/v1/chat/completions').strip()
    path = path if path.startswith('/') else '/' + path
    if base.endswith('/chat/completions'):
        return base
    if path == '/v1/chat/completions' and _re.search(r'/v\d+$', base):
        return base + '/chat/completions'
    return base + path
