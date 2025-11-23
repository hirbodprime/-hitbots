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


def leaderboard(request):
    chat_id = request.GET.get("chat_id")

    # global: best score per user
    global_qs = (
        TetrisScore.objects.values("user_id", "username")
        .annotate(best=Max("score"))
        .order_by("-best")[:10]
    )
    data_global = list(global_qs)

    data_chat = []
    if chat_id:
        chat_qs = (
            TetrisScore.objects.filter(chat_id=chat_id)
            .values("user_id", "username")
            .annotate(best=Max("score"))
            .order_by("-best")[:10]
        )
        data_chat = list(chat_qs)

    return JsonResponse({"global": data_global, "chat": data_chat})


@csrf_exempt
def submit_score(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    data = json.loads(request.body.decode("utf-8"))
    user_id = int(data.get("user_id", 0))
    chat_id = data.get("chat_id")
    username = (data.get("username") or "")[:255]
    score = int(data.get("score", 0))
    message_id = data.get("message_id")
    inline_message_id = data.get("inline_message_id")

    if not user_id:
        return HttpResponseBadRequest("user_id missing")

    # Save to DB (global history)
    TetrisScore.objects.create(
        user_id=user_id,
        chat_id=chat_id or None,
        username=username,
        score=score,
    )

    # Update Telegram per-chat leaderboard (like LumberJack)
    if BOT_TOKEN and score > 0:
        payload = {
            "user_id": user_id,
            "score": score,
            "force": True,          # overwrite lower scores
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
