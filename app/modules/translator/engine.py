import html
import requests
from typing import List, Tuple, Optional

class TranslationEngine:
    """Multi-provider free translation engine (Google Translate, MyMemory)."""

    LANGUAGES = {
        "auto": "🌐 自动检测语言",
        "zh-CN": "🇨🇳 中文 (简体)",
        "zh-TW": "🇨🇳 中文 (繁体)",
        "en": "🇺🇸 英语 (English)",
        "ja": "🇯🇵 日语 (日本語)",
        "ko": "🇰🇷 韩语 (한국어)",
        "fr": "🇫🇷 法语 (Français)",
        "de": "🇩🇪 德语 (Deutsch)",
        "es": "🇪🇸 西班牙语 (Español)",
        "ru": "🇷🇺 俄语 (Русский)",
        "it": "🇮🇹 意大利语 (Italiano)",
        "pt": "🇵🇹 葡萄牙语 (Português)",
        "ar": "🇸🇦 阿拉伯语 (العربية)"
    }

    @classmethod
    def translate_google(cls, text: str, src: str = "auto", dest: str = "zh-CN", proxy: Optional[str] = None) -> str:
        """Translate via Google Translate free mobile endpoint."""
        if not text.strip():
            return ""
        
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": src,
            "tl": dest,
            "dt": "t",
            "q": text
        }
        proxies = {"http": proxy, "https": proxy} if proxy else None
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        resp = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        
        translated_pieces = []
        if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            for part in data[0]:
                if part and len(part) > 0 and part[0]:
                    translated_pieces.append(part[0])
        return "".join(translated_pieces)

    @classmethod
    def translate_mymemory(cls, text: str, src: str = "en", dest: str = "zh-CN", proxy: Optional[str] = None) -> str:
        """Translate via MyMemory free collaborative translation API."""
        if not text.strip():
            return ""
        src_lang = "en" if src == "auto" else src
        langpair = f"{src_lang}|{dest}"
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": langpair}
        proxies = {"http": proxy, "https": proxy} if proxy else None
        headers = {"User-Agent": "Mozilla/5.0"}
        
        resp = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        res_text = data.get("responseData", {}).get("translatedText", "")
        return html.unescape(res_text)

    @classmethod
    def translate_smart(cls, text: str, src: str = "auto", dest: str = "zh-CN", provider: str = "google", proxy: Optional[str] = None) -> str:
        """Intelligently translates text with multi-engine fallback and large paragraph slicing."""
        if not text.strip():
            return ""

        paragraphs = text.split("\n")
        translated_paragraphs = []

        for p in paragraphs:
            if not p.strip():
                translated_paragraphs.append("")
                continue
            
            translated_p = None
            if provider == "google":
                try:
                    translated_p = cls.translate_google(p, src, dest, proxy)
                except Exception:
                    try:
                        translated_p = cls.translate_mymemory(p, src, dest, proxy)
                    except Exception:
                        pass
            else:
                try:
                    translated_p = cls.translate_mymemory(p, src, dest, proxy)
                except Exception:
                    try:
                        translated_p = cls.translate_google(p, src, dest, proxy)
                    except Exception:
                        pass

            if translated_p is None:
                translated_paragraphs.append(f"[网络异常/需代理] {p}")
            else:
                translated_paragraphs.append(translated_p)

        return "\n".join(translated_paragraphs)

    @classmethod
    def align_bilingual_paragraphs(cls, original_text: str, translated_text: str) -> List[Tuple[str, str]]:
        """Aligns original and translated text by paragraph for side-by-side or stacked bilingual comparison."""
        orig_lines = original_text.split("\n")
        trans_lines = translated_text.split("\n")

        max_len = max(len(orig_lines), len(trans_lines))
        pairs = []
        for i in range(max_len):
            o = orig_lines[i] if i < len(orig_lines) else ""
            t = trans_lines[i] if i < len(trans_lines) else ""
            if o.strip() or t.strip():
                pairs.append((o, t))
        return pairs
