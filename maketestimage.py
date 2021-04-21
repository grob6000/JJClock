from PIL import Image

size = (1448,1072)
gridsize = 50

img = Image.new('L', size)
img.paste(0xFF, box=(0,0,size[0],size[1])) # fill white
for y in range(0,int(size[1]/gridsize)+1):
  for x in range(0,int(size[0]/gridsize)+1):
    if (x+y)%2==0: # make an alternating pattern
      img.paste(0x00, box=(x*gridsize,y*gridsize,min((x+1)*gridsize-1,size[0]),min((y+1)*gridsize-1,size[1]))) # draw black squares
img.save('./img/test.png')