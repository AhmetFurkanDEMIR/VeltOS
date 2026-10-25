"""Stand-ins for the AI services: recorded-style SSE streams per service
(a short answer with one tool call, then a closing answer) and an opener
that serves them in order and records the requests. No network."""

import io
import json
import urllib.error


def sse(events):
    lines = []
    for event in events:
        name, data = event if isinstance(event, tuple) else (None, event)
        if name:
            lines.append(f"event: {name}")
        lines.append("data: " + (data if isinstance(data, str) else json.dumps(data)))
        lines.append("")
    return ("\n".join(lines) + "\n").encode("utf-8")


def claude_tool_turn():
    return sse([
        ("message_start", {"type": "message_start", "message": {"id": "msg_1", "role": "assistant", "content": []}}),
        ("content_block_start", {"type": "content_block_start", "index": 0,
                                 "content_block": {"type": "thinking", "thinking": "", "signature": ""}}),
        ("content_block_delta", {"type": "content_block_delta", "index": 0,
                                 "delta": {"type": "signature_delta", "signature": "sig-1"}}),
        ("content_block_stop", {"type": "content_block_stop", "index": 0}),
        ("content_block_start", {"type": "content_block_start", "index": 1,
                                 "content_block": {"type": "text", "text": ""}}),
        ("content_block_delta", {"type": "content_block_delta", "index": 1,
                                 "delta": {"type": "text_delta", "text": "Turning on "}}),
        ("content_block_delta", {"type": "content_block_delta", "index": 1,
                                 "delta": {"type": "text_delta", "text": "Wi-Fi."}}),
        ("content_block_stop", {"type": "content_block_stop", "index": 1}),
        ("content_block_start", {"type": "content_block_start", "index": 2,
                                 "content_block": {"type": "tool_use", "id": "toolu_1", "name": "set_wifi",
                                                   "input": {}}}),
        ("content_block_delta", {"type": "content_block_delta", "index": 2,
                                 "delta": {"type": "input_json_delta", "partial_json": "{\"on\": tr"}}),
        ("content_block_delta", {"type": "content_block_delta", "index": 2,
                                 "delta": {"type": "input_json_delta", "partial_json": "ue}"}}),
        ("content_block_stop", {"type": "content_block_stop", "index": 2}),
        ("message_delta", {"type": "message_delta", "delta": {"stop_reason": "tool_use"}, "usage": {}}),
        ("message_stop", {"type": "message_stop"}),
    ])


def claude_text(text, stop="end_turn"):
    return sse([
        ("message_start", {"type": "message_start", "message": {"id": "msg_2", "role": "assistant", "content": []}}),
        ("content_block_start", {"type": "content_block_start", "index": 0,
                                 "content_block": {"type": "text", "text": ""}}),
        ("content_block_delta", {"type": "content_block_delta", "index": 0,
                                 "delta": {"type": "text_delta", "text": text}}),
        ("content_block_stop", {"type": "content_block_stop", "index": 0}),
        ("message_delta", {"type": "message_delta", "delta": {"stop_reason": stop}, "usage": {}}),
        ("message_stop", {"type": "message_stop"}),
    ])


def openai_tool_turn():
    return sse([
        ("response.created", {"type": "response.created", "response": {"id": "resp_1"}}),
        ("response.output_item.done", {"type": "response.output_item.done", "output_index": 0,
                                       "item": {"type": "reasoning", "id": "rs_1", "encrypted_content": "enc",
                                                "summary": []}}),
        ("response.output_text.delta", {"type": "response.output_text.delta", "delta": "Turning on "}),
        ("response.output_text.delta", {"type": "response.output_text.delta", "delta": "Wi-Fi."}),
        ("response.output_item.done", {"type": "response.output_item.done", "output_index": 1,
                                       "item": {"type": "message", "id": "msg_1", "role": "assistant",
                                                "content": [{"type": "output_text", "text": "Turning on Wi-Fi."}]}}),
        ("response.output_item.done", {"type": "response.output_item.done", "output_index": 2,
                                       "item": {"type": "function_call", "id": "fc_1", "call_id": "call_1",
                                                "name": "set_wifi", "arguments": "{\"on\":true}"}}),
        ("response.completed", {"type": "response.completed", "response": {"id": "resp_1", "status": "completed"}}),
    ])


def openai_text(text):
    return sse([
        ("response.output_text.delta", {"type": "response.output_text.delta", "delta": text}),
        ("response.output_item.done", {"type": "response.output_item.done", "output_index": 0,
                                       "item": {"type": "message", "id": "msg_2", "role": "assistant",
                                                "content": [{"type": "output_text", "text": text}]}}),
        ("response.completed", {"type": "response.completed", "response": {"id": "resp_2"}}),
    ])


def gemini_tool_turn():
    return sse([
        {"candidates": [{"content": {"role": "model", "parts": [{"text": "Turning on "}]}}]},
        {"candidates": [{"content": {"role": "model", "parts": [{"text": "Wi-Fi."}]}}]},
        {"candidates": [{"content": {"role": "model", "parts": [
            {"functionCall": {"name": "set_wifi", "args": {"on": True}}, "thoughtSignature": "sig-g"}]},
            "finishReason": "STOP"}]},
    ])


def gemini_text(text):
    return sse([{"candidates": [{"content": {"role": "model", "parts": [{"text": text}]}, "finishReason": "STOP"}]}])


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class FakeService:
    """Serves the given answers in order; an int answer is an HTTP error
    status, an exception is raised as it is."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.requests = []

    def __call__(self, request, timeout=None):
        body = json.loads(request.data.decode("utf-8")) if request.data else None
        self.requests.append({"url": request.full_url, "headers": dict(request.header_items()), "body": body,
                              "method": request.get_method()})
        answer = self.answers.pop(0)
        if isinstance(answer, int):
            raise urllib.error.HTTPError(request.full_url, answer, "error", {},
                                         io.BytesIO(json.dumps({"error": {"message": "bad key"}}).encode()))
        if isinstance(answer, Exception):
            raise answer
        return Response(answer)
