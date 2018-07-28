import telegram
import requests
import os 

from PIL import Image, ImageEnhance
from pprint import pprint
from telegram.ext import MessageHandler, Filters, Updater

token = 'TOKEN'

batch = int()

def reduce_opacity(im, opacity):
    assert opacity >= 0 and opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im

def watermark(im, mark, opacity=1):
    if opacity < 1:
        mark = reduce_opacity(mark, opacity)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    layer = Image.new('RGBA', im.size, (0,0,0,0))
    ratio = min(
        float(im.size[0]) / mark.size[0], float(im.size[1]) / mark.size[1])
    w = int((mark.size[0] * ratio)/1.5)
    h = int((mark.size[1] * ratio)/1.5)
    mark = mark.resize((w, h), Image.BILINEAR)
    layer.paste(mark, (0, im.size[1]-mark.size[1]))
    return Image.composite(layer, im, layer)

def watermark_bot(bot, update):
	cid = update.message.chat.id
	global batch
	print (batch)
	if batch:
		file = bot.get_file(update.message.document.file_id)
	else:
		file = bot.get_file(update.message.photo[-1].file_id)
	request = requests.get(file['file_path'])
	with open('file.png', 'wb') as f:
		f.write(request.content)
	mark = Image.open('water.png')
	image = Image.open('file.png')
	if batch:
		watermark(image, mark, 0.75).convert('RGB').save('watermarked.jpg', quality=95, optimize=True)
		bot.send_document(cid, open('watermarked.jpg', 'rb'), timeout=300)
		os.remove('watermarked.jpg')
		batch -= 1
	else:
		watermark(image, mark, 0.75).save('watermarked.png', "PNG")
		bot.send_document(cid, open('watermarked.png', 'rb'), timeout=300)
		os.remove('watermarked.png')
	os.remove('file.png')


def beep_bot(bot, update):
	cid = update.message.chat.id
    if update.message.text.lower() == "beep":
        bot.send_message(cid, "`Boop`", parse_mode="Markdown")
    elif update.message.text.lower()[:5] == "batch":
    	global batch
    	batch = int(update.message.text[5:])

updater = Updater(token=token)
dispatcher = updater.dispatcher
pic_handler = MessageHandler((Filters.photo | Filters.document), watermark_bot)
beep_handler = MessageHandler(Filters.text, beep_bot)
dispatcher.add_handler(pic_handler)
dispatcher.add_handler(beep_handler)
updater.start_polling(clean=True)
print ("Running")
updater.idle()
