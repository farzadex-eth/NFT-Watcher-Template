from rest_framework import serializers
from .models import Collection, Watching

class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'slug', 'title', 'address', 'floor', 'updated_at', 'num_watched', 'num_active_targets', 'change', 'last_update']


class TopCollectionsSerializer(serializers.ModelSerializer):
    num_watched = serializers.IntegerField()
    num_active_targets = serializers.IntegerField()
    num_watched_unique = serializers.IntegerField()

    class Meta:
        model = Collection
        fields = ['slug', 'title', 'num_watched', 'num_active_targets', 'num_watched_unique']

class WatchingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Watching
        fields = ['id', 'slug', 'target_type', 'target', 'current', 'user_id']