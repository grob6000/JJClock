from PIL import Image, ImageDraw, ImageFont

size = (1448,1072)
gridsize = 50

bounds = (20,20,1400,1000) # x1, y1, x2, y2
bbox = (bounds[0],bounds[1],bounds[2]-bounds[0],bounds[3]-bounds[1]) # x, y, w, h

# make an image
img = Image.new('L', size)
img.paste(0xDF, box=(0,0,size[0],size[1])) # fill white
draw = ImageDraw.Draw(img)

## checkers
#for y in range(0,int(size[1]/gridsize)+1):
#  for x in range(0,int(size[0]/gridsize)+1):
#    if (x+y)%2==0: # make an alternating pattern
#      img.paste(0x00, box=(x*gridsize,y*gridsize,min((x+1)*gridsize-1,size[0]),min((y+1)*gridsize-1,size[1]))) # draw black squares

# bounding box
draw.rectangle(bounds, fill=0xFF, outline=0x00)

# C/Ls
xcl = round((bounds[0]+bounds[2])/2)
ycl = round((bounds[1]+bounds[3])/2)
draw.line((xcl,bounds[1],xcl,bounds[3]), fill=0x00)
draw.line((bounds[0],ycl,bounds[2],ycl), fill=0x00)

# annotate
tpad = 50
fnt = ImageFont.truetype("./arial.ttf",20)
draw.text((bounds[0]+tpad, ycl),str(bounds[0]),font=fnt,fill=0x00)
draw.text((bounds[2]-tpad, ycl),str(bounds[2]),font=fnt,fill=0x00)
draw.text((xcl, bounds[1]+tpad),str(bounds[1]),font=fnt,fill=0x00)
draw.text((xcl, bounds[3]-tpad),str(bounds[3]),font=fnt,fill=0x00)

# add extra lines
for x in range(bounds[2],size[0],10):
  draw.line((x,0,x,size[1]), fill=0x00)

for y in range(bounds[3],size[1],10):
  draw.line((0,y,size[0],y), fill=0x00)

#img.show()

img.save('./img/test.png')
