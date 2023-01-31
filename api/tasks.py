from django.db.models import Q, F
from django.conf import settings
from celery import shared_task, app
from .models import Collection, Watching
import requests


channel = settings.DISCORD_TARGET_CHANNEL_ID
token = settings.DISCORD_BOT_TOKEN

def send_discord_alert(msg, ids):
    url = "https://discordapp.com/api/channels/{}/messages".format(channel, msg)
    mentions = ""
    for id in ids:
        mentions += "<@{}>, ".format(id)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bot {}".format(token)
    }
    data = {
        "content": mentions + msg,
        "allowed_mentions": {
            "users": [str(id) for id in ids]
        }
    }
    try:
        resp = requests.post(url, headers=headers, json=data)
        return True
    except Exception as e:
        print(e)
        return False

@shared_task
def find_active_watchers(slug, floor):
    coll = Collection.objects.get(slug=slug)

    # value watchers
    cond1 = Q(current__lt=F('target')) & Q(target__lte=floor)
    cond2 = Q(current__gt=F('target')) & Q(target__gte=floor)
    valueWatchers = Watching.objects.filter(slug=coll).filter(target_type=0).filter(cond1 | cond2).filter(active=True)
    wIds = []
    dIds = []
    for w in valueWatchers:
        if w.user_id not in dIds:
            dIds.append(w.user_id)
        wIds.append(w.id)

    if len(wIds) > 0:
        msg = "{} floor price reached {} \nhttps://opensea.io/collection/{}".format(coll.title, floor, coll.slug)
        if send_discord_alert(msg, dIds):
            Watching.objects.filter(id__in=wIds).update(active=False)

    # percentage watchers
    #gone up
    cond3 = Q(target__gte=0) & Q(target__lte=(100*(floor-F('current'))/F('current')))
    percWatchersUp = Watching.objects.filter(slug=coll).filter(target_type=1).filter(cond3).filter(active=True)
    wIds = []
    dIds = []
    for w in percWatchersUp:
        if w.user_id not in dIds:
            dIds.append(w.user_id)
        wIds.append(w.id)

    if len(wIds) > 0:
        msg = "{} floor price has gone up {}% \nhttps://opensea.io/collection/{}".format(coll.title, floor-coll.last_floor/100, coll.slug)
        if send_discord_alert(msg, dIds):
            Watching.objects.filter(id__in=wIds).update(active=False)

    cond4 = Q(target__lt=0) & Q(target__gte=(100*(floor-F('current'))/F('current')))
    percWatchersDown = Watching.objects.filter(slug=coll).filter(target_type=1).filter(cond4).filter(active=True)
    wIds = []
    dIds = []
    for w in percWatchersDown:
        if w.user_id not in dIds:
            dIds.append(w.user_id)
        wIds.append(w.id)

    if len(wIds) > 0:
        msg = "{} floor price has gone down {}% \nhttps://opensea.io/collection/{}".format(coll.title, floor-coll.last_floor/100, coll.slug)
        if send_discord_alert(msg, dIds):
            Watching.objects.filter(id__in=wIds).update(active=False)