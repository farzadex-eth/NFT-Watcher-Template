from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Collection, Watching
from .serializers import CollectionSerializer, WatchingSerializer, TopCollectionsSerializer
import requests
from .osfuncs import opensea_collection_api
from .imagefuncs import create_collection_image


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    http_method_names = ['get', 'post']

    def create(self, request):
        
        try:
            title, address, floor, imageUrl = opensea_collection_api(request.POST["slug"])

            slug = request.POST["slug"]

            Collection.objects.create(
                slug=slug,
                title=title,
                floor=floor,
                last_floor=floor,
                address=address,
                updated_at=timezone.now()
            )

            r = requests.get(imageUrl, stream=True)

            if r.ok:
                with open(settings.APP_DATA_DIRECTORY+"collection-images/{}.avif".format(slug), "wb") as handle:
                    handle.write(r.content)
            create_collection_image(Collection.objects.get(slug=slug))

            response = {"slug": slug, "title": title, "address": address, "floor": floor}
            return Response(response)
        
        except Exception as e:
            return Response({"success": False, "msg": str(e)})


class TopCollectionsViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.annotate(num_watched_unique=Count('watching__user_id', distinct=True)).order_by('-num_watched_unique')[:10]
    serializer_class = TopCollectionsSerializer
    http_method_names = ['get']


class WatchingAddViewSet(viewsets.ModelViewSet):
    queryset = Watching.objects.all()
    serializer_class = WatchingSerializer
    http_method_names = ['post']

    def create(self, request):
        keys = ["slug", "target", "target_type", "user_id"]

        for key in keys:
            if not request.POST[key]:
                response = {"success": False, "msg": "{} not specified".format(key)}
                return Response((response))

        try:
            coll = Collection.objects.get(id=int(request.POST["slug"]))
            target = request.POST["target"]
            targetType = request.POST["target_type"]
            discord = request.POST["user_id"]
            active = True

            Watching.objects.create(
                slug=coll,
                target=target,
                current=coll.floor,
                target_type=targetType,
                user_id=discord
            )

            response = {
                "success": True,
                "slug": coll.slug,
                "target": target,
                "current": coll.floor,
                "target_type": targetType,
                "user_id": discord
            }
            return Response(response)
        except Exception as e:
            response = {"success": False, "msg": str(e)}
            return Response(response)
