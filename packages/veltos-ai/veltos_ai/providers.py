"""The AI services VeltOS AI talks to, each in its own API's words, over
plain HTTPS (urllib: the image takes packages only from Debian, which has
none of the services' SDKs).

- ChatGPT: OpenAI's Responses API (`POST /v1/responses`); the newest GPT
  models call tools only there (OpenAI's changelog, 2026-10).
- Copilot: Microsoft's consumer Copilot has no API key for personal use;
  Microsoft's Azure OpenAI (Foundry) offers the same Responses API at
  `https://<resource>.openai.azure.com/openai/v1/` with the user's key and
  deployment name.
- Claude: Anthropic's Messages API, `anthropic-version: 2026-10-21`.
- Gemini: Google's `streamGenerateContent` (`alt=sse`).

Every request streams (Server-Sent Events). An adapter turns the stream
into ("text", str), ("tool", call), ("end", info) and ("error", info)
events and keeps the assistant's turn exactly as the service sent it
(Claude's thinking blocks with their signatures, OpenAI's reasoning
items, Gemini's thought signatures): the services need them back
unchanged with the tool results. Conversations are stateless: nothing is
stored by the service on VeltOS' behalf (`store: false` for OpenAI).
"""

import json
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "VeltOS-AI/1.0 (+https://veltos.ahmetfurkandemir.com)"
ANTHROPIC_VERSION = "2026-10-21"
FALLBACK_BETA = "server-side-fallback-2026-07-01"

PROVIDERS = {
    # A small model on this PC (local.py, veltos-llama): free, offline, no
    # key; the model is a downloaded GGUF file.
    "local": {"title": "Local model (free, offline)", "model": "gemma-3-270m-it-UD-IQ3_XXS.gguf",
              "prefer": (), "keys": ""},
    "openai": {"title": "ChatGPT (OpenAI)", "model": "gpt-5.5",
               "prefer": ("gpt-6.1-sol", "gpt-6-sol", "gpt-6-luna", "gpt-5.6", "gpt-5.5"),
               "keys": "https://platform.openai.com/api-keys"},
    "claude": {"title": "Claude (Anthropic)", "model": "claude-opus-5-5",
               "prefer": ("claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"),
               "keys": "https://platform.claude.com/"},
    "gemini": {"title": "Gemini (Google)", "model": "gemini-flash-latest",
               "prefer": ("gemini-flash-latest",),
               "keys": "https://aistudio.google.com/apikey"},
    "copilot": {"title": "Copilot (Microsoft Azure OpenAI)", "model": "",
                "prefer": (), "keys": "https://ai.azure.com/"},
}
ORDER = ("local", "openai", "claude", "gemini", "copilot")


class ServiceError(Exception):
    """A failed request: `kind` is key, rate, model, network or other."""

    def __init__(self, kind, detail=""):
        super().__init__(detail or kind)
        self.kind = kind
        self.detail = detail


def classify(status, body):
    """ServiceError for an HTTP error answer."""
    detail = ""
    try:
        data = json.loads(body)
        error = data.get("error") if isinstance(data, dict) else None
        if isinstance(error, dict):
            detail = str(error.get("message") or error.get("status") or "")
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            detail = str((data[0].get("error") or {}).get("message") or "")
        elif error:
            detail = str(error)
    except ValueError:
        detail = body[:300] if isinstance(body, str) else ""
    lowered = detail.lower()
    if status in (401, 403) or "api key" in lowered or "api_key" in lowered:
        return ServiceError("key", detail)
    if status in (429, 529, 503):
        return ServiceError("rate", detail)
    if status == 404 or ("model" in lowered and ("not found" in lowered or "does not exist" in lowered
                                                 or "not supported" in lowered or "invalid" in lowered)):
        return ServiceError("model", detail)
    return ServiceError("other", detail or f"HTTP {status}")


def sse_events(lines):
    """(event, data) pairs of a Server-Sent Events stream (lines as bytes)."""
    event, data = None, []
    for raw in lines:
        line = raw.decode("utf-8", "replace").rstrip("\r\n") if isinstance(raw, bytes) else raw.rstrip("\r\n")
        if line == "":
            if data:
                yield event, "\n".join(data)
            event, data = None, []
            continue
        if line.startswith(":"):
            continue
        field, _, value = line.partition(":")
        if value.startswith(" "):
            value = value[1:]
        if field == "event":
            event = value
        elif field == "data":
            data.append(value)
    if data:
        yield event, "\n".join(data)


def open_request(request, opener=None, timeout=120):
    """The response of a request; ServiceError for errors and no network."""
    try:
        return (opener or urllib.request.urlopen)(request, timeout=timeout)
    except urllib.error.HTTPError as error:
        try:
            body = error.read().decode("utf-8", "replace")
        except OSError:
            body = ""
        raise classify(error.code, body) from error
    except (urllib.error.URLError, OSError) as error:
        raise ServiceError("network", str(getattr(error, "reason", error))) from error


def json_request(url, body, headers, method="POST"):
    data = None if body is None else json.dumps(body).encode("utf-8")
    all_headers = {"User-Agent": USER_AGENT, "Accept": "text/event-stream" if body and body.get("stream")
                   else "application/json"}
    if data is not None:
        all_headers["Content-Type"] = "application/json"
    all_headers.update(headers)
    return urllib.request.Request(url, data=data, headers=all_headers, method=method)


def parse_arguments(raw):
    """A tool call's arguments as a dict, or None when they are not a JSON object."""
    if isinstance(raw, dict):
        return raw
    try:
        value = json.loads(raw) if raw and raw.strip() else {}
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


class Adapter:
    """One service. Subclasses build requests and read their streams."""

    name = ""

    def __init__(self, settings):
        self.key = (settings.get("key") or "").strip()
        self.model = (settings.get("model") or PROVIDERS[self.name]["model"]).strip()
        self.endpoint = (settings.get("endpoint") or "").strip()
        self.turn = []                 # the assistant's turn as the service sent it

    def add_user(self, history, text):
        raise NotImplementedError

    def request(self, history, system, tools):
        raise NotImplementedError

    def read(self, events):
        raise NotImplementedError

    def add_tool_results(self, history, results):
        raise NotImplementedError

    def models_request(self):
        return None

    def models(self, data):
        return []


# --- OpenAI (and Azure OpenAI): the Responses API ------------------------------------------------

class OpenAI(Adapter):
    name = "openai"
    base = "https://api.openai.com/v1"

    def headers(self):
        return {"Authorization": f"Bearer {self.key}"}

    def add_user(self, history, text):
        history.append({"role": "user", "content": text})

    def request(self, history, system, tools):
        body = {"model": self.model, "instructions": system, "input": history, "stream": True, "store": False}
        if tools:
            body["tools"] = [{"type": "function", "name": t["name"], "description": t["description"],
                              "parameters": t["parameters"], "strict": False} for t in tools]
        return json_request(self.base + "/responses", body, self.headers())

    def read(self, events):
        self.turn = []
        stop = "end_turn"
        for event, data in events:
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
            except ValueError:
                continue
            kind = obj.get("type") or event
            if kind in ("response.output_text.delta", "response.refusal.delta"):
                yield "text", obj.get("delta", "")
            elif kind == "response.output_item.done":
                item = obj.get("item") or {}
                self.turn.append(item)
                if item.get("type") == "function_call":
                    arguments = parse_arguments(item.get("arguments"))
                    yield "tool", {"id": item.get("call_id", ""), "name": item.get("name", ""), "input": arguments}
            elif kind == "response.incomplete":
                stop = ((obj.get("response") or {}).get("incomplete_details") or {}).get("reason") or "incomplete"
            elif kind == "response.failed":
                error = (obj.get("response") or {}).get("error") or {}
                yield "error", ServiceError("other", str(error.get("message") or "failed"))
                return
            elif kind == "error":
                message = obj.get("message") or (obj.get("error") or {}).get("message") or "error"
                yield "error", ServiceError("rate" if "rate" in str(message).lower() else "other", str(message))
                return
        yield "end", {"stop": stop}

    def add_tool_results(self, history, results):
        for call, output, _failed in results:
            history.append({"type": "function_call_output", "call_id": call["id"], "output": output})

    def models_request(self):
        return json_request(self.base + "/models", None, self.headers(), method="GET")

    def models(self, data):
        skip = ("embedding", "tts", "whisper", "dall-e", "image", "realtime", "audio", "transcribe", "moderation",
                "search", "babbage", "davinci", "sora", "codex")
        ids = [m.get("id", "") for m in (data or {}).get("data") or []]
        return sorted((i for i in ids if i.startswith(("gpt-", "o")) and not any(s in i for s in skip)),
                      reverse=True)


class Copilot(OpenAI):
    """Microsoft Azure OpenAI's v1 API: the Responses API of the user's
    resource; the model is the deployment's name."""

    name = "copilot"

    @property
    def base(self):
        endpoint = self.endpoint.rstrip("/")
        if endpoint and not endpoint.startswith("https://"):
            endpoint = "https://" + endpoint.removeprefix("http://")
        if endpoint.endswith("/openai/v1"):
            return endpoint
        return endpoint + "/openai/v1"

    def headers(self):
        return {"api-key": self.key}

    def models_request(self):
        return None


# --- Anthropic: the Messages API --------------------------------------------------------------------

class Claude(Adapter):
    name = "claude"
    base = "https://api.anthropic.com/v1"

    def headers(self, fallbacks=False):
        headers = {"x-api-key": self.key, "anthropic-version": ANTHROPIC_VERSION}
        if fallbacks:
            headers["anthropic-beta"] = FALLBACK_BETA
        return headers

    def uses_fallbacks(self):
        # A declined request is retried server-side on the model Anthropic
        # recommends for the refusal's category (Claude API only; not for
        # every model, e.g. not Haiku).
        return self.model.startswith(("claude-opus-5", "claude-sonnet-5-5", "claude-fable-5"))

    def add_user(self, history, text):
        history.append({"role": "user", "content": text})

    def request(self, history, system, tools):
        body = {"model": self.model, "max_tokens": 32000, "stream": True, "system": system, "messages": history}
        if tools:
            # Streamed tool input as it is generated; read() validates it.
            body["tools"] = [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"],
                              "eager_input_streaming": True} for t in tools]
        fallbacks = self.uses_fallbacks()
        if fallbacks:
            body["fallbacks"] = "default"
        return json_request(self.base + "/messages", body, self.headers(fallbacks))

    def read(self, events):
        blocks, order, partial = {}, [], {}
        stop = "end_turn"
        self.turn = []
        for event, data in events:
            try:
                obj = json.loads(data)
            except ValueError:
                continue
            kind = obj.get("type") or event
            if kind == "content_block_start":
                index = obj.get("index", len(order))
                block = dict(obj.get("content_block") or {})
                blocks[index] = block
                order.append(index)
                if block.get("type") == "tool_use":
                    partial[index] = ""
                    block["input"] = {}
                elif block.get("type") == "text" and block.get("text"):
                    yield "text", block["text"]
            elif kind == "content_block_delta":
                index = obj.get("index")
                block = blocks.get(index)
                delta = obj.get("delta") or {}
                if block is None:
                    continue
                kind = delta.get("type")
                if kind == "text_delta":
                    block["text"] = block.get("text", "") + delta.get("text", "")
                    yield "text", delta.get("text", "")
                elif kind == "thinking_delta":
                    block["thinking"] = block.get("thinking", "") + delta.get("thinking", "")
                elif kind == "signature_delta":
                    block["signature"] = block.get("signature", "") + delta.get("signature", "")
                elif kind == "input_json_delta":
                    partial[index] = partial.get(index, "") + delta.get("partial_json", "")
                elif kind == "citations_delta":
                    block.setdefault("citations", []).append(delta.get("citation"))
            elif kind == "content_block_stop":
                index = obj.get("index")
                block = blocks.get(index)
                if block and block.get("type") == "tool_use":
                    arguments = parse_arguments(partial.get(index, ""))
                    block["input"] = arguments if arguments is not None else {}
                    yield "tool", {"id": block.get("id", ""), "name": block.get("name", ""), "input": arguments}
            elif kind == "message_delta":
                stop = (obj.get("delta") or {}).get("stop_reason") or stop
            elif kind == "error":
                error = obj.get("error") or {}
                error_type = str(error.get("type", ""))
                yield "error", ServiceError("rate" if error_type in ("overloaded_error", "rate_limit_error") else "other",
                                            str(error.get("message") or error_type))
                return
        self.turn = [{"role": "assistant", "content": [blocks[i] for i in order]}] if stop != "refusal" else []
        yield "end", {"stop": stop}

    def add_tool_results(self, history, results):
        # All results of one turn in one user message.
        history.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": call["id"], "content": output, "is_error": failed}
            for call, output, failed in results]})

    def models_request(self):
        return json_request(self.base + "/models?limit=100", None, self.headers(), method="GET")

    def models(self, data):
        return [m.get("id", "") for m in (data or {}).get("data") or [] if m.get("id", "").startswith("claude-")]


# --- Google: Gemini's generateContent -------------------------------------------------------------

REFUSAL_FINISH = ("SAFETY", "RECITATION", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "IMAGE_SAFETY")


class Gemini(Adapter):
    name = "gemini"
    base = "https://generativelanguage.googleapis.com/v1beta"

    def headers(self):
        return {"x-goog-api-key": self.key}

    def add_user(self, history, text):
        history.append({"role": "user", "parts": [{"text": text}]})

    def request(self, history, system, tools):
        body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": history}
        if tools:
            declarations = []
            for t in tools:
                declaration = {"name": t["name"], "description": t["description"]}
                if t["parameters"].get("properties"):
                    declaration["parameters"] = t["parameters"]
                declarations.append(declaration)
            body["tools"] = [{"functionDeclarations": declarations}]
        model = urllib.parse.quote(self.model.removeprefix("models/"), safe="-._")
        request = json_request(f"{self.base}/models/{model}:streamGenerateContent?alt=sse", body, self.headers())
        request.add_header("Accept", "text/event-stream")
        return request

    def read(self, events):
        parts = []
        stop = "end_turn"
        count = 0
        for _event, data in events:
            try:
                obj = json.loads(data)
            except ValueError:
                continue
            if obj.get("error"):
                error = obj["error"]
                yield "error", classify(int(error.get("code") or 500), json.dumps({"error": error}))
                return
            if (obj.get("promptFeedback") or {}).get("blockReason"):
                stop = "refusal"
            for candidate in (obj.get("candidates") or [])[:1]:
                for part in (candidate.get("content") or {}).get("parts") or []:
                    # Parts are kept as they came (thought signatures included);
                    # plain text pieces are joined.
                    if set(part) == {"text"} and parts and set(parts[-1]) == {"text"}:
                        parts[-1] = {"text": parts[-1]["text"] + part["text"]}
                    else:
                        parts.append(dict(part))
                    if "text" in part and not part.get("thought"):
                        yield "text", part["text"]
                    if "functionCall" in part:
                        call = part["functionCall"] or {}
                        count += 1
                        yield "tool", {"id": call.get("id") or f"call_{count}", "name": call.get("name", ""),
                                       "input": parse_arguments(call.get("args") or {}), "gemini_id": call.get("id")}
                finish = candidate.get("finishReason")
                if finish in REFUSAL_FINISH:
                    stop = "refusal"
                elif finish == "MAX_TOKENS":
                    stop = "max_tokens"
        self.turn = [{"role": "model", "parts": parts}] if parts and stop != "refusal" else []
        yield "end", {"stop": stop}

    def add_tool_results(self, history, results):
        parts = []
        for call, output, failed in results:
            response = {"name": call["name"], "response": {"error" if failed else "result": output}}
            if call.get("gemini_id"):
                response["id"] = call["gemini_id"]
            parts.append({"functionResponse": response})
        history.append({"role": "user", "parts": parts})

    def models_request(self):
        return json_request(self.base + "/models?pageSize=200", None, self.headers(), method="GET")

    def models(self, data):
        found = []
        for model in (data or {}).get("models") or []:
            if "generateContent" in (model.get("supportedGenerationMethods") or []):
                name = model.get("name", "").removeprefix("models/")
                if name.startswith("gemini"):
                    found.append(name)
        return sorted(found, reverse=True)


# --- The local model: llama-server's OpenAI-compatible Chat Completions -----------------------------

class Local(Adapter):
    """llama.cpp's server on 127.0.0.1 (local.Server starts it with the
    chosen model). Plain chat: a model this small does not call tools."""

    name = "local"
    system = ("You are VeltOS AI, a helpful assistant on a VeltOS computer. Answer in the language the user "
              "writes in, briefly and politely.")

    def __init__(self, settings, server=None):
        super().__init__(settings)
        from . import local
        self.local = local
        self.server = server or local.SERVER_INSTANCE

    def add_user(self, history, text):
        history.append({"role": "user", "content": text})

    def request(self, history, system, tools):
        path = self.local.model_path(self.model)
        if path is None:
            raise ServiceError("model", self.model)
        try:
            base = self.server.base(path)
        except self.local.DownloadError as error:
            raise ServiceError("local", str(error)) from error
        body = {"model": self.model, "stream": True, "temperature": 0.7, "max_tokens": 1024,
                "messages": [{"role": "system", "content": self.system}] + history[-12:]}
        return json_request(base + "/v1/chat/completions", body, {})

    def read(self, events):
        text, stop = "", "end_turn"
        for _event, data in events:
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
            except ValueError:
                continue
            for choice in obj.get("choices") or []:
                delta = (choice.get("delta") or {}).get("content") or ""
                if delta:
                    text += delta
                    yield "text", delta
                if choice.get("finish_reason") == "length":
                    stop = "max_tokens"
        self.turn = [{"role": "assistant", "content": text}] if text else []
        yield "end", {"stop": stop}

    def add_tool_results(self, history, results):
        pass


ADAPTERS = {"local": Local, "openai": OpenAI, "copilot": Copilot, "claude": Claude, "gemini": Gemini}


def adapter(provider, settings):
    return ADAPTERS[provider](settings)


def stream(adapter_, history, system, tools, opener=None, cancelled=lambda: False):
    """Runs one request and yields its events; stops reading when cancelled."""
    response = open_request(adapter_.request(history, system, tools), opener)
    try:
        def lines():
            for line in response:
                if cancelled():
                    return
                yield line
        yield from adapter_.read(sse_events(lines()))
    finally:
        try:
            response.close()
        except OSError:
            pass


def list_models(adapter_, opener=None):
    request = adapter_.models_request()
    if request is None:
        return []
    with open_request(request, opener, timeout=30) as response:
        try:
            data = json.loads(response.read().decode("utf-8"))
        except ValueError as error:
            raise ServiceError("other", "not JSON") from error
    return adapter_.models(data)


def pick_model(provider, available, current=""):
    """The model to use: the current one if offered, else the first preferred one."""
    if current and current in available:
        return current
    for preferred in PROVIDERS[provider]["prefer"]:
        if preferred in available:
            return preferred
    return current or (available[0] if available else PROVIDERS[provider]["model"])
