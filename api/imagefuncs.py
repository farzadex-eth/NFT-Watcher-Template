from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
from django.db.models import F
from django.conf import settings
from .models import Watching

def create_collection_image(coll):
    image = Image.new('RGB', (1280, 720), color="white")
    draw = ImageDraw.Draw(image)
    draw.text((100, 10), coll.title + " (slug: {})".format(coll.slug), fill="black", font=ImageFont.truetype('/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf', 20))
    draw.text((100, 400), coll.address, fill="black", font=ImageFont.truetype('/usr/share/fonts/truetype/ubuntu/Ubuntu-M.ttf', 18))
    draw.text((100, 450), 'floor price: {}'.format(coll.floor), fill="black", font=ImageFont.truetype('/usr/share/fonts/truetype/ubuntu/Ubuntu-M.ttf', 20))
    draw.text((100, 500), 'last update: {}'.format(coll.updated_at.strftime("%d %B %Y %H:%M:%S UTC")), fill="black", font=ImageFont.truetype('/usr/share/fonts/truetype/ubuntu/Ubuntu-M.ttf', 20))
    draw.text((100, 550), 'No. Unique Watchers: {}'.format(coll.num_watched_unique()), fill="black", font=ImageFont.truetype('/usr/share/fonts/truetype/ubuntu/Ubuntu-M.ttf', 20))
    draw.text((100, 600), 'No. Total Watched: {}'.format(coll.num_watched()), fill="black", font=ImageFont.truetype('/usr/share/fonts/truetype/ubuntu/Ubuntu-M.ttf', 20))
    draw.text((100, 650), 'No. Active Targets: {}'.format(coll.num_active_targets()), fill="black", font=ImageFont.truetype('/usr/share/fonts/truetype/ubuntu/Ubuntu-M.ttf', 20))

    collImg = Image.open(settings.APP_DATA_DIRECTORY+"collection-images/{}.avif".format(coll.slug))
    collImg = collImg.resize((250, 250))
    image.paste(collImg, (100, 100))

    create_target_hist(coll)
    histImg = Image.open(settings.APP_DATA_DIRECTORY+"collection-images/hist-{}.png".format(coll.slug))
    image.paste(histImg, (600, 100))

    image.save(settings.APP_DATA_DIRECTORY+'collection-images/collection-{}.png'.format(coll.slug))


def create_target_hist(coll):
    targets = Watching.objects.filter(slug=coll, target_type=0, active=True).values('target')
    percTargets = Watching.objects.filter(slug=coll, target_type=1, active=True).annotate(perc_target_val=F('current')*(1+F('target')/100)).values('perc_target_val')
    targets = [target['target'] for target in targets]
    for pt in percTargets:
        targets.append(pt['perc_target_val'])

    plt.clf()
    plt.title("Current Targets (total: {})".format(len(targets)))
    plt.xlabel('Number of Targets')
    plt.ylabel('Target Price')
    if len(targets) == 0:
        plt.ylim((coll.floor*0.9, coll.floor*1.1))
        plt.axhline(y=coll.floor, color='black', linestyle='--')
        plt.text(1, coll.floor, 'floor : {:.4f}'.format(coll.floor), fontsize=10, ha='center', backgroundcolor='white')
        plt.savefig(settings.APP_DATA_DIRECTORY+'collection-images/hist-{}.png'.format(coll.slug))
        return
    minValue = min(min(targets), coll.floor)
    maxValue = max(max(targets), coll.floor)
    higher = [x for x in targets if x>coll.floor]
    lower = [x for x in targets if x<coll.floor]
    max1 = 0
    max2 = 0
    if len(higher) > 0:
        hist1 = plt.hist(higher, bins=10, orientation='horizontal', range=(coll.floor, maxValue), align='mid', color='green')
        max1 = max(hist1[0])
        for i in range(10):
            if hist1[0][i] > 0:
                y = hist1[1][i]
                plt.text(hist1[0][i], y, '{:.4f}'.format(y), fontsize=8, ha='left')
    if len(lower) > 0:
        hist2 = plt.hist(lower, bins=10, orientation='horizontal', range=(minValue, coll.floor), align='mid', color='red')
        max2 = max(hist2[0])
        for i in range(10):
            if hist2[0][i] > 0:
                y = hist2[1][i]
                plt.text(hist2[0][i], y, '{:.4f}'.format(y), fontsize=8, ha='left')

    plt.xticks(range(0, int(max(max1, max2))+1))
    plt.axhline(y=coll.floor, color='black', linestyle='--')
    plt.text((max(max1, max2)+1)/2, coll.floor, 'floor : {:.4f}'.format(coll.floor), fontsize=10, ha='center', backgroundcolor='white')
    plt.savefig(settings.APP_DATA_DIRECTORY+'collection-images/hist-{}.png'.format(coll.slug))