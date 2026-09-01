import html
import json
import re
import urllib.parse
import requests
from typing import List, Tuple, Optional, Dict, Any

class TranslationEngine:
    """Universal multi-provider translation engine with zero-config free public APIs + Custom AI LLM support."""

    PROVIDERS = {
        "bing": "🟢 微软 Bing 翻译 (国内直连·免Key)",
        "youdao": "🟢 有道 智能翻译 (国内直连·免Key)",
        "baidu": "🟢 百度 极速翻译 (国内直连·免Key)",
        "google": "🔵 谷歌 Google 翻译 (需代理/海外)",
        "mymemory": "🔵 MyMemory 翻译 (开源多语种)",
        "custom_llm": "🤖 自定义 AI 大模型翻译"
    }

    @classmethod
    def get_provider_display_name(cls, provider_key: str, model_name: Optional[str] = None) -> str:
        """Dynamically returns the provider display label reflecting the actual selected AI model name."""
        if provider_key == "custom_llm":
            if model_name and model_name.strip():
                return f"🤖 AI 大模型 ({model_name.strip()})"
            return "🤖 自定义 AI 大模型翻译"
        return cls.PROVIDERS.get(provider_key, "未知翻译引擎")

    LANGUAGES = {
        "auto": "🌐 自动检测语言",
        "zh-CN": "🇨🇳 中文 (简体)",
        "zh-TW": "🇨🇳 中文 (繁体)",
        "en": "🇺🇸 英语 (English)",
        "ja": "🇯🇵 日语 (日本語)",
        "ko": "🇰🇷 韩语 (한국어)",
        "vi": "🇻🇳 越南语 (Tiếng Việt)",
        "th": "🇹🇭 泰语 (ไทย)",
        "id": "🇮🇩 印尼语 (Bahasa Indonesia)",
        "ms": "🇲🇾 马来语 (Bahasa Melayu)",
        "tl": "🇵🇭 菲律宾语 (Tagalog)",
        "my": "🇲🇲 缅甸语 (မြန်မာ)",
        "km": "🇰🇭 高棉语 (ភាសាខ្មែរ)",
        "lo": "🇱🇦 老挝语 (ພາສາລາວ)",
        "fr": "🇫🇷 法语 (Français)",
        "de": "🇩🇪 德语 (Deutsch)",
        "es": "🇪🇸 西班牙语 (Español)",
        "ru": "🇷🇺 俄语 (Русский)",
        "it": "🇮🇹 意大利语 (Italiano)",
        "pt": "🇵🇹 葡萄牙语 (Português)",
        "nl": "🇳🇱 荷兰语 (Nederlands)",
        "pl": "🇵🇱 波兰语 (Polski)",
        "el": "🇬🇷 希腊语 (Ελληνικά)",
        "tr": "🇹🇷 土耳其语 (Türkçe)",
        "uk": "🇺🇦 乌克兰语 (Українська)",
        "cs": "🇨🇿 捷克语 (Čeština)",
        "sv": "🇸🇪 瑞典语 (Svenska)",
        "da": "🇩🇰 丹麦语 (Dansk)",
        "fi": "🇫🇮 芬兰语 (Suomi)",
        "no": "🇳🇴 挪威语 (Norsk)",
        "hu": "🇭🇺 匈牙利语 (Magyar)",
        "ro": "🇷🇴 罗马尼亚语 (Română)",
        "ar": "🇸🇦 阿拉伯语 (العربية)",
        "fa": "🇮🇷 波斯语 (فارسی)",
        "hi": "🇮🇳 印地语 (हिन्दी)",
        "he": "🇮🇱 希伯来语 (עברית)",
        "bn": "🇧🇩 孟加拉语 (বাংলা)",
        "ur": "🇵🇰 乌尔都语 (اردو)",
        "la": "🇻🇦 拉丁语 (Latina)",
        "eo": "🌐 世界语 (Esperanto)"
    }

    @classmethod
    def translate_bing(cls, text: str, src: str = "auto", dest: str = "zh-CN", proxy: Optional[str] = None) -> str:
        """Bing / Edge translator public web endpoint (Direct domestic connectivity)."""
        if not text.strip():
            return ""
        
        # Edge translation endpoint
        url = "https://api-edge.cognitive.microsofttranslator.com/translate"
        src_param = "" if src == "auto" else f"&from={src.split('-')[0]}"
        dest_lang = "zh-Hans" if dest in ("zh-CN", "zh") else ("zh-Hant" if dest == "zh-TW" else dest.split("-")[0])
        full_url = f"{url}?api-version=3.0&to={dest_lang}{src_param}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Referer": "https://www.bing.com/"
        }
        body = [{"Text": text}]
        proxies = {"http": proxy, "https": proxy} if proxy else None

        resp = requests.post(full_url, json=body, headers=headers, proxies=proxies, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data and isinstance(data, list) and "translations" in data[0]:
            return data[0]["translations"][0].get("text", "")
        return ""

    @classmethod
    def translate_youdao(cls, text: str, src: str = "auto", dest: str = "zh-CN", proxy: Optional[str] = None) -> str:
        """Youdao dict public translation endpoint (Fast domestic connection, good for code/tech)."""
        if not text.strip():
            return ""
        
        url = "https://aidemo.youdao.com/trans"
        src_lang = "auto" if src == "auto" else (src.split("-")[0].upper())
        tgt_lang = "zh-CHS" if dest in ("zh-CN", "zh") else (dest.split("-")[0].upper())
        data = {"q": text, "from": src_lang, "to": tgt_lang}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://ai.youdao.com/"
        }
        proxies = {"http": proxy, "https": proxy} if proxy else None

        resp = requests.post(url, data=data, headers=headers, proxies=proxies, timeout=10)
        resp.raise_for_status()
        res_json = resp.json()
        trans = res_json.get("translation", [])
        if trans and isinstance(trans, list):
            return "\n".join(trans)
        return ""

    @classmethod
    def translate_baidu(cls, text: str, src: str = "auto", dest: str = "zh-CN", proxy: Optional[str] = None) -> str:
        """Baidu simple public translate endpoint."""
        if not text.strip():
            return ""
        url = "https://fanyi.baidu.com/transapi"
        from_lang = "auto" if src == "auto" else src.split("-")[0]
        to_lang = "zh" if dest in ("zh-CN", "zh") else dest.split("-")[0]
        data = {
            "from": from_lang,
            "to": to_lang,
            "query": text,
            "source": "txt"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://fanyi.baidu.com"
        }
        proxies = {"http": proxy, "https": proxy} if proxy else None
        resp = requests.post(url, data=data, headers=headers, proxies=proxies, timeout=10)
        resp.raise_for_status()
        res_json = resp.json()
        items = res_json.get("data", [])
        if items and isinstance(items, list):
            return "\n".join([item.get("dst", "") for item in items])
        return ""

    @classmethod
    def translate_google(cls, text: str, src: str = "auto", dest: str = "zh-CN", proxy: Optional[str] = None) -> str:
        """Google Translate mobile endpoint."""
        if not text.strip():
            return ""
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": src, "tl": dest, "dt": "t", "q": text}
        proxies = {"http": proxy, "https": proxy} if proxy else None
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        pieces = []
        if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            for part in data[0]:
                if part and len(part) > 0 and part[0]:
                    pieces.append(part[0])
        return "".join(pieces)

    @classmethod
    def translate_mymemory(cls, text: str, src: str = "en", dest: str = "zh-CN", proxy: Optional[str] = None) -> str:
        """MyMemory collaborative translation API."""
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
        return html.unescape(data.get("responseData", {}).get("translatedText", ""))

    OFFLINE_MODEL_PRESETS = {
        "deepseek": ["deepseek-chat", "deepseek-reasoner", "deepseek-coder"],
        "dashscope": ["qwen-plus", "qwen-max", "qwen-turbo", "qwen-long", "qwen2.5-72b-instruct", "qwen2.5-32b-instruct"],
        "openai": ["gpt-4o", "gpt-4o-mini", "o1", "o3-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "moonshot": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "bigmodel": ["glm-4-flash", "glm-4-plus", "glm-4-air", "glm-4-long", "glm-4"],
        "openrouter": ["openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet", "deepseek/deepseek-chat", "meta-llama/llama-3.3-70b-instruct", "google/gemini-flash-1.5"],
        "ollama": ["qwen2.5:latest", "deepseek-r1:latest", "llama3.2:latest", "mistral:latest", "gemma2:latest"]
    }

    @classmethod
    def get_offline_preset_models(cls, base_url: str) -> List[str]:
        """Returns preset list of popular official models if API key is not yet configured or connection fails."""
        u = base_url.lower()
        if "deepseek" in u:
            return cls.OFFLINE_MODEL_PRESETS["deepseek"]
        if "dashscope" in u or "aliyun" in u:
            return cls.OFFLINE_MODEL_PRESETS["dashscope"]
        if "openai" in u:
            return cls.OFFLINE_MODEL_PRESETS["openai"]
        if "moonshot" in u or "kimi" in u:
            return cls.OFFLINE_MODEL_PRESETS["moonshot"]
        if "bigmodel" in u or "zhipu" in u:
            return cls.OFFLINE_MODEL_PRESETS["bigmodel"]
        if "openrouter" in u:
            return cls.OFFLINE_MODEL_PRESETS["openrouter"]
        if "11434" in u or "ollama" in u:
            return cls.OFFLINE_MODEL_PRESETS["ollama"]
        return ["deepseek-chat", "gpt-4o-mini", "qwen-plus", "glm-4-flash", "custom-model"]

    @classmethod
    def fetch_remote_models(cls, base_url: str, api_key: str = "", proxy: Optional[str] = None) -> Tuple[List[str], bool]:
        """Fetches the list of available model IDs. Returns (models_list, is_live_online).
        If API Key is missing or service requires auth, falls back gracefully to offline official model presets."""
        url = base_url.strip().rstrip("/")
        if not url:
            url = "https://api.deepseek.com/v1"

        # If user has not provided an API Key and it's not a local Ollama service, immediately provide official presets
        is_local = "127.0.0.1" in url or "localhost" in url
        if not api_key.strip() and not is_local:
            return cls.get_offline_preset_models(url), False

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SuperTools/2.0"
        }
        if api_key.strip():
            headers["Authorization"] = f"Bearer {api_key.strip()}"

        proxies = {"http": proxy, "https": proxy} if proxy else None

        # 1. Try standard OpenAI /v1/models
        endpoints_to_try = []
        if url.endswith("/models"):
            endpoints_to_try.append(url)
        else:
            endpoints_to_try.append(f"{url}/models")

        # If it's local Ollama, also try /api/tags
        if is_local:
            root_url = url.replace("/v1", "").rstrip("/")
            endpoints_to_try.append(f"{root_url}/api/tags")

        last_err = None
        for ep in endpoints_to_try:
            try:
                resp = requests.get(ep, headers=headers, proxies=proxies, timeout=6)
                if resp.status_code == 200:
                    data = resp.json()
                    models = []
                    # Parse standard OpenAI format or Ollama tags format
                    if isinstance(data, dict):
                        items = data.get("data") or data.get("models") or []
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict):
                                    m_name = item.get("id") or item.get("name") or item.get("model")
                                    if m_name:
                                        models.append(str(m_name))
                                elif isinstance(item, str):
                                    models.append(item)
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "id" in item:
                                models.append(str(item["id"]))
                            elif isinstance(item, str):
                                models.append(item)

                    valid_models = sorted(list(set(models)))
                    if valid_models:
                        return valid_models, True
            except Exception as e:
                last_err = e

        # Fallback to rich official preset list
        return cls.get_offline_preset_models(url), False

    @classmethod
    def translate_custom_llm(cls, text: str, src: str = "auto", dest: str = "zh-CN", api_key: str = "", base_url: str = "", model: str = "", proxy: Optional[str] = None) -> str:
        """Translates via OpenAI-compatible AI API (DeepSeek, Qwen, ChatGPT, Ollama)."""
        if not text.strip():
            return ""
        
        endpoint = base_url.rstrip("/") + "/chat/completions" if base_url else "https://api.deepseek.com/v1/chat/completions"
        model_name = model or "deepseek-chat"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}" if api_key else ""
        }
        dest_name = cls.LANGUAGES.get(dest, dest)
        prompt = (
            f"You are a professional technical translator. Translate the following text into {dest_name}. "
            f"Preserve formatting, technical jargon, code blocks, and markdown structure accurately. "
            f"Output ONLY the translation result without any conversational preamble or explanations.\n\nText:\n{text}"
        )
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
        proxies = {"http": proxy, "https": proxy} if proxy else None
        resp = requests.post(endpoint, json=payload, headers=headers, proxies=proxies, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    @classmethod
    def translate_smart(
        cls, 
        text: str, 
        src: str = "auto", 
        dest: str = "zh-CN", 
        provider_key: str = "bing", 
        proxy: Optional[str] = None,
        llm_config: Optional[Dict[str, str]] = None
    ) -> str:
        """Dispatches translation to chosen provider with intelligent multi-engine fallback."""
        if not text.strip():
            return ""

        paragraphs = text.split("\n")
        translated_paragraphs = []

        def _do_translate_single(p_text: str) -> Optional[str]:
            if not p_text.strip():
                return ""
            
            # Primary choice
            if provider_key == "bing":
                try: return cls.translate_bing(p_text, src, dest, proxy)
                except Exception: pass
            elif provider_key == "youdao":
                try: return cls.translate_youdao(p_text, src, dest, proxy)
                except Exception: pass
            elif provider_key == "baidu":
                try: return cls.translate_baidu(p_text, src, dest, proxy)
                except Exception: pass
            elif provider_key == "google":
                try: return cls.translate_google(p_text, src, dest, proxy)
                except Exception: pass
            elif provider_key == "mymemory":
                try: return cls.translate_mymemory(p_text, src, dest, proxy)
                except Exception: pass
            elif provider_key == "custom_llm" and llm_config:
                try: 
                    return cls.translate_custom_llm(
                        p_text, src, dest, 
                        api_key=llm_config.get("api_key", ""), 
                        base_url=llm_config.get("base_url", ""), 
                        model=llm_config.get("model", ""), 
                        proxy=proxy
                    )
                except Exception: pass

            # Automatic Fallbacks (Bing -> Youdao -> Baidu -> Google -> MyMemory)
            for fn in (cls.translate_bing, cls.translate_youdao, cls.translate_baidu, cls.translate_google, cls.translate_mymemory):
                try:
                    res = fn(p_text, src, dest, proxy)
                    if res: return res
                except Exception:
                    continue
            return None

        for p in paragraphs:
            if not p.strip():
                translated_paragraphs.append("")
                continue
            res = _do_translate_single(p)
            if res is None:
                translated_paragraphs.append(f"[翻译网络异常: 请切换引擎或检查网络] {p}")
            else:
                translated_paragraphs.append(res)

        return "\n".join(translated_paragraphs)

    @classmethod
    def align_bilingual_paragraphs(cls, original_text: str, translated_text: str) -> List[Tuple[str, str]]:
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
