from jjrenderer.renderer import *

import random
import importlib
import logging
import datetime

## LANGUAGE NUMBER ELEMENTS ##

numberstrings_en = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
decadestrings_en = ["Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
monthstrings_en = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

numberstrings_de = ["null", "ein", "zwei", "drei", "vier", "funf", "sechs", "sieben", "acht", "neun", "zehn", "elf", "zwölf", "dreizehn", "vierzehn", "funfzehn", "sechzehn", "siebzehn", "achtzehn", "neunzehn"]
decadestrings_de = ["zwanzig", "dreizig", "vierzig", "funfzig", "sechzig", "siebzig", "achtzig", "neunzig"]

numberstrings_es = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce", "trece", "catorce", "quince", "dieceséis", "diecisiete", "dieciocho", "diecinueve", "viente", "vientiuno", "vientidós", "vientitrés", "vienticuatro", "vienticinco", "vientiséis", "vientisiete", "vientiocho", "vientinueve"]
decadestrings_es = ["viente", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]

numberstrings_fr = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
decadestrings_fr = ["vingt", "trente", "quarante", "cinguante"]

numberstrings_it = ["?", "uno", "due", "tre", "quattro", "cinque", "sei", "sette", "otto", "nove", "dieci", "undici", "dodici", "tredici", "quattordici", "quindici", "sedici", "diciassette", "diciotto", "diciannove"]
decadestrings_it = ["venti", "trenta", "quaranta", "cinquanta", "sesanta", "settanta", "ottanta", "novanta"]

numberstrings_et = ["null", "üks", "kaks", "kolm", "neli", "viis", "kuus", "seitse", "kaheksa", "üheksa", "kümme", "üksteist", "kaksteist", "kolmteist", "neliteist", "viisteist", "kussteist", "seitseteist", "kaheksateist", "üheksateist"]
decadestrings_et = ["kakskümmend", "kolmkümmend", "nelikümmend", "viiskümmend", "kuuskümmend", "seitsekümmend", "kaheksakümmend" "üheksakümmend"]

def GetNumberString(n, lang="en"):

	if lang == "de":
		numberstrings = numberstrings_de
		decadestrings = decadestrings_de
	elif lang == "es":
		numberstrings = numberstrings_es
		decadestrings = decadestrings_es
	elif lang == "fr":
		numberstrings = numberstrings_fr
		decadestrings = decadestrings_fr
	elif lang == "it":
		numberstrings = numberstrings_it
		decadestrings = decadestrings_it
	elif lang == "et":
		numberstrings = numberstrings_et
		decadestrings = decadestrings_et
	else:
		numberstrings = numberstrings_en
		decadestrings = decadestrings_en
		
	if n < 0 or n > 99:
		print("error - number out of supported range")
		return ""
	
	if lang == "es":
		if n < 30:
			s = numberstrings[n]
		else:
			d = n // 10
			i = n % 10
			s = numberstrings[i]+" y "+decadestrings[d-2]
	else:
		if n < 20:
			s = numberstrings[n]
		else:
			d = n // 10
			i = n % 10
			s = decadestrings[d-2]
			if i > 0:
				if lang == "de":
					s = numberstrings[i]+"und"+s
				elif lang == "it":
					if i == 1 or i == 8:
						s = s[0:len(s)-1] #apcocope for uno, otto
					s += numberstrings[i]
				elif lang == "fr" and i == 1:
					s += " et un"
				elif lang == "et":
					s += " " + numberstrings[i]
				else:
					s += "-" + numberstrings[i]
	return s
    
def GetDateString(dt, lang="en"):
	monthstrings = monthstrings_en
	return str(dt.day) + " " + monthstrings[dt.month - 1] + " " + str(dt.year)

def GetHourString(h, lang="en", format="12h"):
	# if it's midday or middnight, 50% chance of using these terms
	r = random.randint(0,1)
	if h == 0 and r == 1:
		if lang == "de":
			hourstring = "Mitternacht"
		else:
			hourstring = "Midnight"
	elif h == 12 and r == 1:
		if lang == "de":
			hourstring = "Mittag"
		else:
			hourstring = "Midday"
	else:
		if format == "24h":
			hourstring = GetNumberString(h % 24, lang)
		else:
			if h == 0:
				h += 12
			hourstring = GetNumberString(h % 12, lang)
	return hourstring    

def GetTimeString(dt=datetime.datetime.now(), lang="en"):
	timestring = ""
	# prepare for 12h times with only numbers
	h = dt.hour % 12
	if h == 0:
		h = 12
	h1 = (dt.hour + 1) % 12
	if h1 == 0:
		h1 = 12
    
	if lang == "en":
		# English wot yurright guvvna
		while timestring == "":
			r = random.randint(0,5)
			if r == 0 and dt.minute > 0:
				# type 0: "mmm past hhh"
				timestring = GetNumberString(dt.minute) + " Past " + GetHourString(dt.hour)
			elif r == 1 and dt.minute % 15 == 0:
				# type 1: o'clock, quarter past, half past, quarter to
				if dt.minute == 0:
					timestring = GetNumberString(h, lang) + " O'Clock"
				elif dt.minute == 15:
					timestring = "Quarter Past " + GetHourString(dt.hour, "en")
				elif dt.minute == 30:
					timestring = "Half Past " + GetHourString(dt.hour)
				elif dt.minute == 45:
					timestring = "Quarter To " + GetHourString(dt.hour + 1)
			elif r == 2 and dt.minute > 9:
				# type 2: "hhh mmm"
				h = dt.hour
				if h == 0:
					h += 12
				timestring = GetNumberString(h) + " " + GetNumberString(dt.minute)
			elif r == 3:
				# type 3: military
				if dt.hour < 10:
					timestring = "Zero "
				timestring += GetNumberString(dt.hour)
				if dt.minute == 0:
					timestring += " Hundred"
				else:
					if dt.minute < 10:
						timestring += " Zero"
					timestring += " " + GetNumberString(dt.minute)
				# randomly determine if we're in the army or navy
				r2 = random.randint(0,1)
				if r2 == 1:
					timestring += " Hours"
			elif r == 4 and dt.minute >= 35:
				# type 4: "mmm [Minutes ]To hhh"
				r2 = random.randint(0,1)
				if r2 == 1:
					midtext = " Minutes To "
				else:
					midtext = " To "
				timestring = GetNumberString(60-dt.minute) + midtext + GetHourString(dt.hour + 1)
			elif r == 5:
				# type 5 special cases
				if dt.hour == 0 and dt.minute == 0:
					timestring = "Midnight"
				elif dt.hour == 12 and dt.minute == 0:
					r2 = random.randint(0,1)
					if r2 == 1:
						timestring = "Midday"
					else:
						timestring = "Noon"
				elif dt.minute == 30:
					# Hear Ye Hear Ye Me Half Ten Yorright Guvvna?
					h = dt.hour
					if h == 0:
						h += 12
					timestring = "Half " + GetNumberString(h)
	elif lang=="de":
		# Deutsche, mein Kommandant
		timestring = "Es ist "
		while timestring == "Es ist ":
			r2 = random.randint(0,4)
			if r2 == 0:
				# "Es ist funfzehn Uhr[ zwei]" ** 24H **
				timestring += GetNumberString(dt.hour, "de") + " Uhr"
				if dt.minute > 0:
					timestring += " " + GetNumberString(dt.minute, "de")
			elif r2 == 1 and dt.minute % 15 == 0:
				# "Es ist [viertel nach / halb / viertel vor] zwei"
				if dt.minute == 0:
					timestring += "um " + GetNumberString(dt.hour, "de")
				elif dt.minute == 15:
					timestring += "Viertel nach " + GetHourString(dt.hour, "de", "12h")
				elif dt.minute == 30:
					timestring += "halb " + GetNumberString(h1, "de")
				elif dt.minute == 45:
					timestring += "Viertel vor " + GetHourString(dt.hour+1, "de", "12h")
				elif dt.minute >= 25 and dt.minute < 30:
					# zwei vor halb seiben
					timestring += GetNumberString(30-dt.minute, "de") + " vor halb " + GetNumberString(h1, "de")
				elif dt.minute <= 35 and dt.minute > 30:
					timestring += GetNumberString(dt.minute-30, "de") + " nach halb " + GetNumberString(h1, "de")	
			elif r2 == 2 and dt.minute > 0:
				# "Es ist zwei nach elf
				r3 = random.randint(0,1)
				if r3 == 1 or dt.hour == 12 or dt.hour == 0:
					timestring += GetNumberString(dt.minute, "de") + " nach " + GetHourString(dt.hour, "de", "12h")
			elif r2 == 3 and dt.minute > 30:
				# "Es ist funfundzwanzig vor ein
				r3 = random.randint(0,1)
				if r3 == 1 or dt.hour == 12 or dt.hour == 0:
					timestring += GetNumberString(60-dt.minute, "de") + " vor " + GetHourString(dt.hour+1, "de", "12h")
			elif r2 == 4:
				# Kurz vor halb acht
				if dt.minute < 5:
					timestring += "Kurz nach um " + GetHourString(dt.hour, "de", "12h")
				elif dt.minute > 25 and dt.minute < 30:
					timestring += "Kurz vor halb " + GetNumberString(h1, "de")
				elif dt.minute > 30 and dt.minute < 35:
					timestring += "Kurz nach halb " + GetNumberString(h1, "de")
				elif dt.minute > 55:
					timestring += "Kurz vor um " + GetNumberString(h1, "de")
	elif lang == "es":
		# espanol mamacita
		r2 = random.randint(0,1)
		if r2 == 1 and dt.minute > 30:
			# to the hour
			if h == 1:
				timestring = "Es la "
			else:
				timestring = "Son las "
			timestring += GetNumberString(h1, "es") + " menos " + GetNumberString(60-dt.minute, "es")
		else:
			# after the hour
			if h1 == 1:
				timestring = "Es la "
			else:
				timestring = "Son las "		
			r3 = random.randint(0,2)
			timestring += GetNumberString(h, "es")
			if dt.minute > 0:
				timestring += " "
				if r3 == 1:
					timestring += "y "
				elif r3 == 2:
					timestring += "con "
				timestring += GetNumberString(dt.minute, "es")
		timestring = timestring.title()
		timestring.replace(" Y ", " y ")
	elif lang == "fr":
		# francois messeur
		timestring = "Il est "
		if dt.minute == 15:
			timestring += GetNumberString(h, "fr") + " et quart"
		elif dt.minute == 30:
			timestring += GetNumberString(h, "fr") + " et demie"
		elif dt.minute == 45:
			timestring += GetNumberString(h1, "fr") + " moins le quart" 
		elif dt.minute >= 40:
			timestring += GetNumberString(h1, "fr") + " moins " + GetNumberString(60-dt.minute, "fr")
		else:
			timestring += GetNumberString(h, "fr")
			if h == 1:
				timestring += " heure " 
			else:
				timestring += " heures"
			if not dt.minute == 0:
				timestring += " " + GetNumberString(dt.minute, "fr")
		if dt.hour < 12:
			timestring += " du matin"
		elif dt.hour < 18:
			timestring += " de l'aprés-midi"
		else:
			timestring += " du soir"
	elif lang == "it":
		# italian *hand waving*
		timestring = "Sono le "
		if dt.minute == 0:
			timestring += GetNumberString(h, "it")
		elif dt.minute == 15:
			timestring += GetNumberString(h, "it") + " e un quarto"
		elif dt.minute == 30:
			timestring += GetNumberString(h, "it") + " e mezza"
		elif dt.minute == 45:
			timestring += GetNumberString(h1, "it") + " meno un quarto"
		elif dt.minute >= 40:
			timestring += GetNumberString(h1, "it") + " meno " + GetNumberString(60-dt.minute, "it")
		else:
			timestring += GetNumberString(h, "it") + " e " + GetNumberString(dt.minute, "it")
	elif lang == "ee":
		# estonian
		timestring = "Kell on "
		if dt.minute == 0:
			timestring += GetNumberString(h, "et")
		elif dt.minute == 15:
			timestring += "veerand " + GetNumberString(h1, "et")
		elif dt.minute == 30:
			timestring += "pool " + GetNumberString(h1, "et")
		elif dt.minute == 45:
			timestring += "kolmveerand " + GetNumberString(h1, "et")
		elif dt.minute >= 40:
			timestring += GetNumberString(h1, "et") + " meno " + GetNumberString(60-dt.minute, "et")
		else:
			timestring += GetNumberString(h, "et") + " " + GetNumberString(dt.minute, "et")
		if dt.hour == 0 and dt.minute == 0:
			timestring += " keskpäev"
		elif dt.hour < 12:
			timestring += " hommikul"
		elif dt.hour == 12 and dt.minute == 0:
			timestring += " kesköö"
		elif dt.hour < 17:
			timestring += " pärastlõunal"
		elif dt.hour < 20:
			timestring += " õhtul"
		else:
			timestring += " öösel"
			
	return timestring
    
class RendererEuroClock(Renderer):
  
  def getName(self):
    return "clock_euro"
  def getMenuItem(self):
    return {"icon":"eu.png","text":"Euro"}
  def doRender(self, screen, **kwargs):
    if len(styles) > 0:
      r = random.randint(0,len(styles)-1) # select a random style
      return styles[r].doRender(self, screen, **kwargs) # pass the render down to the selected style
    else:
      return super().doRender(screen, **kwargs) # use default...
    
class _StyleFrench(RendererEuroClock):
  def doRender(self, screen, **kwargs):
  
    # get time-related text
    t = "Je ne connais pas l'heure"
    d = "Aujourd'hui"
    if "timestamp" in kwargs and kwargs["timestamp"]:
      t = GetTimeString(kwargs["timestamp"], lang="fr")
      d = GetDateString(kwargs["timestamp"], lang="fr")
    logging.info("time: {0}, date: {1}".format(t,d))
    
    fill(screen)
    
    draw = ImageDraw.Draw(screen)
    pad = 50
    y = 100
    
    # logo
    logomaxheight = 150
    logomaxwidth = 800
    logo = getImage("logo_lemonde")
    s = 1.0
    if logo.size[1]/logo.size[0] > logomaxheight/logomaxwidth:
      s = logomaxheight/logo.size[1]
    else:
      s = logomaxwidth/logo.size[0]
    logo = logo.resize((int(logo.size[0]*s), int(logo.size[1]*s)),Image.ANTIALIAS)
    screen.paste(logo,(int(screen.size[0]/2 - logo.size[0]/2),y))
    y = y + logo.size[1] + pad
    
    # intermediate bar
    barheight = 100
    screen.paste(0x80, box=(100, y, screen.size[0]-100, y+barheight))
    y = y + barheight + pad
    
    # date bar
    datefont = getFont("arialnarrow", 24)
    dsz = datefont.getsize(d)
    draw.text((100,y),d,font=datefont,fill=0x00)
    
    # headline
    headlinemaxwidth = screen.size[0] - 200
    headlinefont = getFont("arialnarrow", 150)
    tsz = headlinefont.getsize(t)
    headlineimg = Image.new("L", tsz)
    fill(headlineimg)
    d2 = ImageDraw.Draw(headlineimg)
    d2.text((0,0),t,font=headlinefont,fill=0x00)
    if tsz[0] > headlinemaxwidth:
      headlineimg = headlineimg.resize((headlinemaxwidth, headlineimg.size[1]))
    screen.paste(headlineimg, (int(screen.size[0]/2 - headlineimg.size[0]/2),int(100+logo.size[1]+pad*1.5+barheight)))
    return screen

# automated luxury space communist style collection
styles = []
l = locals().copy()
for name, obj in l.items():
  if name.startswith("_Style"):
    styles.append(obj)
logging.debug("euro styles loaded: " + str(styles))