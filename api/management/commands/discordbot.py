from django.core.management.base import BaseCommand
from django.conf import settings
import interactions
from interactions import Button, ButtonStyle, autodefer, SelectOption, SelectMenu, Choice, spread_to_rows
from interactions.api.models.misc import File
from asgiref.sync import sync_to_async
from api.models import Collection, Watching
import json
import os
import requests
from django.utils import timezone
from api.imagefuncs import create_collection_image
from api.osfuncs import parse_opensea_resp, opensea_collection_api
from api.serializers import CollectionSerializer

token = settings.DISCORD_BOT_TOKEN
guild = settings.DISCORD_GUILD_ID

class Command(BaseCommand):
    help = "run discord bot"

    def handle(self, *args, **options):

        #create images folder
        try:
            os.mkdir(settings.APP_DATA_DIRECTORY)
        except Exception as e:
            print(e)
        try:
            os.mkdir(settings.APP_DATA_DIRECTORY+'collection-images')
        except Exception as e:
            print(e)


        bot = interactions.Client(token=token)

        @bot.command(
            name="ping",
            description="Simple ping command",
            scope=guild
        )
        async def ping(ctx: interactions.CommandContext):
            await ctx.send("pong", ephemeral=True)


        def get_collection_data(name):
            coll = None
            try:
                coll = Collection.objects.get(slug__iexact=name)
            except:
                try:
                    coll = Collection.objects.get(title__iexact=name)
                except:
                    pass
            
            if not coll:
                raise Exception("Not Found")

            ser = CollectionSerializer(coll)
            return json.dumps(ser.data)

        def get_collection_instance(name):
            coll = None
            try:
                coll = Collection.objects.get(slug__iexact=name)
            except:
                try:
                    coll = Collection.objects.get(title__iexact=name)
                except:
                    pass
            
            if not coll:
                raise Exception("Not Found")

            return coll

        def collection_exists(slug):
            try:
                Collection.objects.get(slug=slug)
                return True
            except:
                return False

        def create_collection_from_url(url):
            slug = url.split('/')[-1]
            slug = slug.split('?')[0]

            if collection_exists(slug):
                return slug

            openSeaResp = opensea_collection_api(slug)

            try:
                success = openSeaResp["success"]
                return None
            except:
                try:
                    title, address, floor, imageUrl = openSeaResp
                except:
                    return None

                coll = Collection.objects.filter(slug=slug)
                if coll:
                    last = coll.floor
                    Collection.objects.filter(slug=slug).update(
                        title=title,
                        floor=floor,
                        last_floor=last,
                        address=address,
                        updated_at=timezone.now()
                    )
                else:
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

                return slug

        class MaxNumberError(Exception):
            "You can only have 3 active targets on each collection"
            pass

        def create_watching_target(coll, user_id, target_type, target, current):
            userCollWatches = Watching.objects.filter(slug=coll, user_id=user_id, active=True)
            if len(userCollWatches) > 2:
                raise MaxNumberError
            Watching.objects.create(
                slug=coll,
                user_id=user_id,
                target_type=target_type,
                target=target,
                current=current
            )


        @bot.command(
            name="collection",
            description="fetch collection",
            scope=guild,
            options= [
                interactions.Option(
                    name="name",
                    description="Collection Slug/Name",
                    type=interactions.OptionType.STRING,
                    required=True,
                ),
            ],
        )
        async def collection_get(ctx: interactions.CommandContext, name: str):
            try:
                data = await sync_to_async(get_collection_data)(name)
                imgName = json.loads(data)
                imgName = imgName['slug']
                img = File(filename=settings.APP_DATA_DIRECTORY+'collection-images/collection-{}.png'.format(imgName))

                await ctx.send(
                    '''Add a target using command: /create_target <collection_slug> <target_type> <target>
                        * target_type:
                            value: a price value
                            percentage: price change percentage (can be negative or positive value)
                        * target: 
                            you can enter a price value like '0.69'
                            or enter a percentage of price change like '10' or '-10'
                    ''',
                     files=[img,],
                     ephemeral=True
                )

            except Exception as e:
                print(e)
                b2 = Button(
                    style = ButtonStyle.PRIMARY,
                    label="Add Collection",
                    custom_id="add_btn"
                )

                await ctx.send("Collection not found in our database!\n You can add it using the collection's OpenSea URL or Slug\nexample: 'https://opensea.io/collection/ens' or 'ens'", components=b2, ephemeral=True)

        @bot.component('add_btn')
        async def add_collection(ctx):
            urlInput = interactions.TextInput(
                style=interactions.TextStyleType.SHORT,
                label="Collection OpenSea URL or Opensea Slug",
                description="example: https://opensea.io/collection/ens or ens",
                custom_id="url_input_response",
                min_length=1,
                max_length=1024,
            )
            modal = interactions.Modal(
                title="Add Collection To Database",
                custom_id="collection_add_form",
                components=[urlInput],
            )
            await ctx.popup(modal)

        

        @bot.modal("collection_add_form")
        async def collection_search(ctx: interactions.CommandContext, url: str):
            collFound = await sync_to_async(create_collection_from_url)(url)
            if collFound != None:
                data = await sync_to_async(get_collection_data)(collFound)
                imgName = json.loads(data)
                imgName = imgName['slug']
                img = File(filename=settings.APP_DATA_DIRECTORY+'collection-images/collection-{}.png'.format(imgName))
                await ctx.send('''
                        Collection added successfuly!
                        Add a target using command: /create_target <collection_slug> <target_type> <target>
                        * target_type:
                            value: a price value
                            percentage: price change percentage (can be negative or positive value)
                        * target: 
                            you can enter a price value like '0.69'
                            or enter a percentage of price change like '10' or '-10'
                    ''', files=[img,], ephemeral=True)
            else:
                await ctx.send("Wrong URL!", ephemeral=True)



        
        @bot.command(
            name="create_target",
            description="create target for collection",
            scope=guild,
            options= [
                interactions.Option(
                    name="name",
                    description="Collection Slug/Name",
                    type=interactions.OptionType.STRING,
                    required=True,
                ),
                interactions.Option(
                    name="target_type",
                    description="Price Value / Percentage",
                    type=interactions.OptionType.INTEGER,
                    required=True,
                    choices=[
                        Choice(name="Value", value=0),
                        Choice(name="Percentage", value=1)
                    ]
                ),
                interactions.Option(
                    name="target",
                    description="target value",
                    type=interactions.OptionType.NUMBER,
                    required=True,
                ),
            ],
        )
        async def create_target_command(ctx, name: str, target_type: int, target: float):
            try:
                coll = await sync_to_async(get_collection_instance)(name)

                await sync_to_async(create_watching_target)(coll, str(ctx.user.id), int(target_type), target, coll.floor)

                msg = "Target Added to collection name: {}, target: {}".format(name, str(target) if target_type == 0 else str(target)+"%")

                await ctx.send(msg, ephemeral=True)
            
            except MaxNumberError:
                await ctx.send("You can only have 3 active targets on each collection", ephemeral=True)

            except Exception as e:
                # print(e)
                await ctx.send("Something went wrong! Please try again!", ephemeral=True)

    
        bot.start()


