from PIL import Image, ImageDraw, ImageFont
from math import ceil

#size = (1448,1072)
gridsize = 50

#cropbox = (10,10,1410,1060) # x1, y1, x2, y2
#bbox = (cropbox[0],cropbox[1],cropbox[2]-cropbox[0],cropbox[3]-cropbox[1]) # x, y, w, h

screensize = (1448, 1072) # Set the width and height of the screen [width, height]
display_vcom = -2.55 # v - as per cable
cropbox = (10,10,1410,1060) # area we should work within / x1, y1, x2, y2
boxsize = (cropbox[2]-cropbox[0],cropbox[3]-cropbox[1]) # x,y
clx = int((cropbox[2] + cropbox[0])/2)
cly = int((cropbox[3] + cropbox[1])/2)

menusize = (4,3)
menupatchsize = (200,200)
menuicondim = 120
menuitemselected = 7

menu = [
         {"icon":"./img/wifi.png","text":"Config Mode","mode":"wificonfig"},
         {"icon":"./img/eu.png","text":"Euro","mode":"clock_euro"},
         {"icon":"./img/uk.png","text":"Brexit","mode":"clock_brexit"},
         {"icon":"./img/digital.png","text":"Digital","mode":"clock_digital"},
         {"icon":"./img/wifi.png","text":"Config Mode","mode":"wificonfig"},
         {"icon":"./img/wifi.png","text":"Config Mode","mode":"wificonfig"},
         {"icon":"./img/wifi.png","text":"Config Mode","mode":"wificonfig"},
         {"icon":"./img/wifi.png","text":"Config Mode","mode":"wificonfig"},
         {"icon":"./img/wifi.png","text":"Config Mode","mode":"wificonfig"},
         {"icon":"./img/wifi.png","text":"Config Mode","mode":"wificonfig"},
         {"icon":"./img/wifi.png","text":"Config Mode","mode":"wificonfig"},
         {"icon":"./img/wifi.png","text":"Config Mode","mode":"wificonfig"},
       ]

def displayImage(img):
  img.show()
  
def showMenu():
  global menuitemselected
  global menu
  global menusize
  global menupatchsize
  global menuicondim
  
  ipp = menusize[0] * menusize[1] # number of items per page
  page = int(menuitemselected / ipp)
  pi_select = menuitemselected % ipp # index of item selected on page
  
  fnt = ImageFont.truetype("./font/ebgaramondmedium.ttf",20)
  
  screen = Image.new('L', boxsize)
  screen.paste(0xFF, box=(0,0,screen.size[0],screen.size[1]))
  
  for pi in range(0, ipp):
    mi = pi+(page*ipp)
    if len(menu) > mi:
      menuimg = Image.new('L', menupatchsize)
      menuimg.paste(0xFF, box=(0,0,menuimg.size[0],menuimg.size[1]))
      menuimg.paste(Image.open(menu[mi]["icon"]).resize((menuicondim,menuicondim),Image.ANTIALIAS),(int((menupatchsize[0]-menuicondim)/2),20))
      draw = ImageDraw.Draw(menuimg)
      fsz = fnt.getsize(menu[mi]["text"])
      draw.text((int(menuimg.size[0]/2-fsz[0]/2), menuicondim + 30),menu[mi]["text"],font=fnt,fill=0x00)
      x = int((pi % menusize[0] + 0.5) * (screen.size[0] / menusize[0]) - menupatchsize[0]/2)
      y = int((int(pi / menusize[0]) + 0.5) * (screen.size[1] / menusize[1]) - menupatchsize[1]/2)
      if pi == pi_select: # show this item as selected with surrounding box
        screen.paste(0x80, box=(x-20, y-20, x+menupatchsize[0]+20, y+menupatchsize[1]+20))
      screen.paste(menuimg, (x,y))
  
  draw = ImageDraw.Draw(screen)
  pagetext = "Page {0} of {1}".format(page+1, ceil(len(menu)/ipp))
  ptsz = fnt.getsize(pagetext)
  draw.text((int(screen.size[0]/2-ptsz[0]/2), 20), pagetext, font=fnt, fill=0x00)
  
  displayImage(screen)

def showNotImplemented(mode="unknown"):
  global boxsize
  screen = Image.new('L', boxsize)
  screen.paste(0xFF, box=(0,0,screen.size[0],screen.size[1]))
  draw = ImageDraw.Draw(screen)
  fnt = ImageFont.truetype("./font/ebgaramondmedium.ttf",20)
  t = "Uh-oh. '" + mode + "' has not been implemented!"
  tsz = fnt.getsize(t)
  draw.text((screen.size[0]/2-tsz[0]/2, screen.size[1]/2-tsz[1]/2), t, font=fnt, fill=0x00)
  displayImage(screen)
  
# make an image
img = Image.new('L', screensize)
img.paste(0xDF, box=(0,0,screensize[0],screensize[1])) # fill white
draw = ImageDraw.Draw(img)

## checkers
#for y in range(0,int(screensize[1]/gridsize)+1):
#  for x in range(0,int(screensize[0]/gridsize)+1):
#    if (x+y)%2==0: # make an alternating pattern
#      img.paste(0x00, box=(x*gridsize,y*gridsize,min((x+1)*gridsize-1,screensize[0]),min((y+1)*gridsize-1,screensize[1]))) # draw black squares

# bounding box
draw.rectangle(cropbox, fill=0xFF, outline=0x00)

# C/Ls
xcl = round((cropbox[0]+cropbox[2])/2)
ycl = round((cropbox[1]+cropbox[3])/2)
draw.line((xcl,cropbox[1],xcl,cropbox[3]), fill=0x00)
draw.line((cropbox[0],ycl,cropbox[2],ycl), fill=0x00)

# annotate
tpad = 50
fnt = ImageFont.truetype("./arial.ttf",20)
draw.text((cropbox[0]+tpad, ycl),str(cropbox[0]),font=fnt,fill=0x00)
draw.text((cropbox[2]-tpad, ycl),str(cropbox[2]),font=fnt,fill=0x00)
draw.text((xcl, cropbox[1]+tpad),str(cropbox[1]),font=fnt,fill=0x00)
draw.text((xcl, cropbox[3]-tpad),str(cropbox[3]),font=fnt,fill=0x00)

# add extra lines
for x in range(cropbox[2],screensize[0],10):
  draw.line((x,0,x,screensize[1]), fill=0x00)

for y in range(cropbox[3],screensize[1],10):
  draw.line((0,y,screensize[0],y), fill=0x00)

#img.show()

img.save('./img/test.png')

screensize = (1448, 1072) # Set the width and height of the screen [width, height]
display_vcom = -2.55 # v - as per cable
cropbox = (10,10,1410,1060) # area we should work within / x1, y1, x2, y2
boxsize = (cropbox[2]-cropbox[0],cropbox[3]-cropbox[1]) # x,y
clx = int((cropbox[2] + cropbox[0])/2)
cly = int((cropbox[3] + cropbox[1])/2)

showMenu()
showNotImplemented("testmode")

