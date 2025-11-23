from django.shortcuts import render
import json
import os
import requests
from django.db.models import Max
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import TetrisScore

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")  # set in .env

def tetris_page(request):
    """
    HTML5 game page.
    Telegram opens this URL as a Game WebView.
    Supports:
    - user_id
    - chat_id
    - username
    - message_id             (for normal chat messages)
    - inline_message_id      (for inline messages)
    """

    user_id = request.GET.get("user_id") or "0"
    chat_id = request.GET.get("chat_id") or "0"
    username = request.GET.get("username", "") or ""
    message_id = request.GET.get("message_id") or "0"
    inline_message_id = request.GET.get("inline_message_id") or ""

    context = {
        "user_id": user_id,
        "chat_id": chat_id,
        "username": username,
        "message_id": message_id,
        "inline_message_id": inline_message_id,
    }

    return render(request, "tetris/index.html", context)



BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
@csrf_exempt
def submit_score(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    user_id = int(data.get("user_id") or 0)
    chat_id = data.get("chat_id")
    username = (data.get("username") or "")[:255]
    score = int(data.get("score") or 0)
    message_id = data.get("message_id")
    inline_message_id = data.get("inline_message_id")

    if not user_id or score <= 0:
        return HttpResponseBadRequest("Missing user_id or score")

    # ---------- ONE ROW PER (user_id, chat_id) – keep BEST score ----------
    chat_key = chat_id or None  # normalize empty to NULL in DB

    obj, created = TetrisScore.objects.get_or_create(
        user_id=user_id,
        chat_id=chat_key,
        defaults={"username": username, "score": score},
    )

    if not created:
        # Only update if new score is higher
        if score > obj.score:
            obj.score = score
            obj.username = username  # keep latest username
            obj.save(update_fields=["score", "username"])
    # ---------------------------------------------------------------------

    # update per-chat leaderboard in Telegram
    if BOT_TOKEN:
        payload = {
            "user_id": user_id,
            "score": score,
            "force": True,
            "disable_edit_message": False,
        }
        if inline_message_id:
            payload["inline_message_id"] = inline_message_id
        elif chat_id and message_id:
            payload["chat_id"] = chat_id
            payload["message_id"] = message_id

        try:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/setGameScore",
                json=payload,
                timeout=5,
            )
        except requests.RequestException:
            pass

    return JsonResponse({"ok": True})

from django.db.models import Q
from .models import TetrisScore

def leaderboard(request):
    chat_id = request.GET.get("chat_id")

    # GLOBAL: take best scores across all rows (we already store only best per user+chat)
    global_qs = (
        TetrisScore.objects
        .order_by("-score")[:10]
    )

    data_global = [
        {
            "user_id": obj.user_id,
            "username": obj.username,
            "best": obj.score,
        }
        for obj in global_qs
    ]

    # THIS CHAT: only if chat_id provided (group chat)
    data_chat = []
    if chat_id:
        data_chat = [
            {
                "user_id": obj.user_id,
                "username": obj.username,
                "best": obj.score,
            }
            for obj in TetrisScore.objects
                .filter(chat_id=chat_id)
                .order_by("-score")[:10]
        ]

    return JsonResponse({"global": data_global, "chat": data_chat})
