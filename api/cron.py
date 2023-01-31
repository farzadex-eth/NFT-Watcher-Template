from .models import Collection
from django.utils import timezone
import requests
import timeit
from .tasks import find_active_watchers
from .osfuncs import opensea_collection_api
from .imagefuncs import create_collection_image


def update_collections():
    collections = Collection.objects.all()
    for collection in collections:
        startTime = timeit.default_timer()
        try:
            slug = collection.slug
            last = collection.floor

            openSeaResp = opensea_collection_api(slug)
            try:
                success = openSeaResp['success']
                print(timezone.now(), " : ", slug + ' - Error!')
            except:
                title, address, floor, imageUrl = openSeaResp
                Collection.objects.filter(slug=slug).update(
                    title=title,
                    floor=floor,
                    last_floor=last,
                    address=address,
                    updated_at=timezone.now()
                )
                print(timezone.now(), " : ", slug + ' - Updated - ', 'floor = ', floor, ' - executed in ', timeit.default_timer()-startTime)
                try:
                    find_active_watchers(slug, floor)
                except Exception as e:
                    print('*************** ', str(e))
                
        except Exception as e:
            print(timezone.now(), " : ", str(e))

def update_collection_image():
    collections = Collection.objects.all()
    for collection in collections:
        try:
            create_collection_image(collection)
        except Exception as e:
            print(e)