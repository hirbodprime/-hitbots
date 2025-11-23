import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import TetrisScore


def tetris_page(request):
    """
    HTML5 game page.
    Telegram will open this URL as a Game (webview).
    We expect ?user_id=&chat_id=&username=
    """
    user_id = request.GET.get("user_id")
    chat_id = request.GET.get("chat_id")
    username = request.GET.get("username", "")

    context = {
        "user_id": user_id,
        "chat_id": chat_id,
        "username": username,
    }
    return render(request, "tetris/index.html", context)


@csrf_exempt
def submit_score(request):
    """
    Called via fetch() from JS when the game ends or score updates.
    Expects JSON:
      {"user_id": ..., "chat_id": ..., "username": "...", "score": ...}
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    user_id = data.get("user_id")
    chat_id = data.get("chat_id")
    username = data.get("username", "")
    score = data.get("score")

    if user_id is None or chat_id is None or score is None:
        return HttpResponseBadRequest("Missing fields")

    obj, created = TetrisScore.objects.get_or_create(
        user_id=user_id,
        chat_id=chat_id,
        defaults={"username": username, "best_score": score},
    )

    if not created and score > obj.best_score:
        obj.best_score = score
        if username:
            obj.username = username
        obj.save()

    return JsonResponse({"ok": True, "best_score": obj.best_score})
