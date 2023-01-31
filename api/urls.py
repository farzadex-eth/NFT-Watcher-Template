from django.urls import path
from rest_framework import routers
from django.conf.urls import include
from .views import CollectionViewSet, WatchingAddViewSet, TopCollectionsViewSet


router = routers.DefaultRouter()
router.register('collections', CollectionViewSet)
router.register('addwatch', WatchingAddViewSet)
router.register('top', TopCollectionsViewSet)

urlpatterns = [
    path('/', include(router.urls)),
]