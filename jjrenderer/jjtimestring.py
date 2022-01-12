import datetime
import logging
import random

## LANGUAGE NUMBER ELEMENTS ##

numberstrings_en = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
decadestrings_en = ["twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
monthstrings_en = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
daystrings_en = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

numberstrings_de = ["null", "ein", "zwei", "drei", "vier", "funf", "sechs", "sieben", "acht", "neun", "zehn", "elf", "zwölf", "dreizehn", "vierzehn", "funfzehn", "sechzehn", "siebzehn", "achtzehn", "neunzehn"]
decadestrings_de = ["zwanzig", "dreizig", "vierzig", "funfzig", "sechzig", "siebzig", "achtzig", "neunzig"]
monthstrings_de = ["januar", "februar", "märz", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "dezember"]
daystrings_de = ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag"]

numberstrings_es = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce", "trece", "catorce", "quince", "dieceséis", "diecisiete", "dieciocho", "diecinueve", "viente", "vientiuno", "vientidós", "vientitrés", "vienticuatro", "vienticinco", "vientiséis", "vientisiete", "vientiocho", "vientinueve"]
decadestrings_es = ["viente", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
monthstrings_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre" ]
daystrings_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

numberstrings_fr = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
decadestrings_fr = ["vingt", "trente", "quarante", "cinguante"]
monthstrings_fr = ["janvier", "février", "mars", "avril", "mai", "juin", "juilliet", "août", "septembre", "octobre", "novembre", "décembre"]
daystrings_fr = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

numberstrings_it = ["?", "uno", "due", "tre", "quattro", "cinque", "sei", "sette", "otto", "nove", "dieci", "undici", "dodici", "tredici", "quattordici", "quindici", "sedici", "diciassette", "diciotto", "diciannove"]
decadestrings_it = ["venti", "trenta", "quaranta", "cinquanta", "sesanta", "settanta", "ottanta", "novanta"]

numberstrings_et = ["null", "üks", "kaks", "kolm", "neli", "viis", "kuus", "seitse", "kaheksa", "üheksa", "kümme", "üksteist", "kaksteist", "kolmteist", "neliteist", "viisteist", "kussteist", "seitseteist", "kaheksateist", "üheksateist"]
decadestrings_et = ["kakskümmend", "kolmkümmend", "nelikümmend", "viiskümmend", "kuuskümmend", "seitsekümmend", "kaheksakümmend" "üheksakümmend"]
daystrings_et = ["esmaspäev", "teisipäev", "kolmapäev", "neljapäev", "reede", "laupäev", "pühapäev"]

daystrings_ru = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
monthstrings_ru = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "сентябрь", "октябрь", "ноябрь", "декабрь"]

languages = ["en", "de", "es", "fr", "it", "et", "ru"]
"""List of currently supported language codes"""

def HalfAndHalf(sentence):
  """Splits a string into two lines. DEPRECATED - please use SplitSentence(sentence, 2)
  
  Keyword Arguments:
  sentence -- string to split in two
  
  Returns:
  list object: ["first line", "second line"]"""
  #sentence = str(sentence)
  #imin = len(sentence)
  #for i in range(0,len(sentence)):
  #  if sentence[i] == " ":
  #    if abs(i - len(sentence)/2) < abs(imin-len(sentence)/2):
  #      imin = i
  #r = [sentence[:imin],sentence[imin+1:]]
  #logging.debug("halfandhalf: " + str(r))
  #return r
  return SplitSentence(sentence, 2)
      
def SplitSentence(sentence, n=2):
  """Splits a string into n lines.
  
  Keyword Arguments:
  sentence -- string to split in two
  n - number of lines to split into

  Returns:
  list object: ["first line", "second line", ... , "nth line"]"""    
  sentence = str(sentence)
  n = int(n)
  r = []
  if n < 2:
      r.append(sentence)
      return r
  for n1 in range(n,0,-1):
    imin = len(sentence)
    if n1 > 1:
      for i in range(0,len(sentence)):
        if sentence[i] == " ":
          if abs(i - len(sentence)/n1) < abs(imin-len(sentence)/n1):
            imin = i
      r.append(sentence[:imin])
      sentence = sentence[imin+1:]
    else:
      r.append(sentence)
  logging.debug("splitsentence: " + str(r))
  return r

def GetNumberString(n, lang="en"):
    """Gets a number from 0-99 written out in the specified language.
    
    Keyword Arguments:
    n -- integer 0-99, to be written out (REQUIRED)
    lang -- string, two-letter code for language to use (default = "en")
    
    See jjtimestring.languages for list of supported languages"""
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

def GetDayOfWeek(dt, lang="en"):
    daystrings = daystrings_en
    if lang == "de":
        daystrings = daystrings_de
    elif lang == "es":
        daystrings = daystrings_es
    elif lang == "fr":
        daystrings = daystrings_fr
    elif lang == "et":
        daystrings = daystrings_et
    return daystrings[dt.weekday()]
    
def GetDateString(dt, lang="en", includeday=False):
    """Gets a date written out in the specified language.
    
    Keyword Arguments:
    dt -- datetime.datetime, containing date to be written out (REQUIRED)
    lang -- string, two-letter code for language to use (default = "en")
    includeday -- whether to include the day (default = False)
    
    See jjtimestring.languages for list of supported languages"""
    if lang == "fr":
      monthstrings = monthstrings_fr
      daystrings = daystrings_fr
    else:
      monthstrings = monthstrings_en
      daystrings = daystrings_en
    s = ""
    if lang == "fr":
      s = "{0}, {1} {2} {3}".format(daystrings[dt.weekday()], dt.day, monthstrings[dt.month - 1], dt.year)
    elif lang == "ru":
      s = "{0} {1} {2} года".format(dt.day, monthstrings_ru[dt.month], dt.year)
      if includeday:
        s = daystrings_ru[dt.weekday()] + ", " + s
    elif lang == "es":
      s = "{0} de {1} de {2}".format(dt.day, monthstrings_es[dt.month-1].title(), dt.year)
      if (includeday):
        s = daystrings_es[dt.weekday()] + " " + s
    else: # en
      s = str(dt.day) + " " + monthstrings[dt.month - 1].title() + " " + str(dt.year)
      if (includeday):
        s = daystrings[dt.weekday()].title() + ", " + s
    return s

def GetHourString(h, lang="en", format="12h"):
    """Gets the hour written out in the specified language.
    
    Keyword Arguments:
    h -- integer, hour from 0-23, to be written out (REQUIRED)
    lang -- string, two-letter code for language to use (default = "en")
    format -- string, either "12h" for 12-hour format, or "24h" for 24h format (default = "12h")

    See jjtimestring.languages for list of supported languages
    Note also supports "en_mil" (military time) and "en_idiomatic" (crappy approximate time)"""
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
        h = h % 12
        if h == 0:
          h = 12
        hourstring = GetNumberString(h, lang)
    return hourstring    

def GetTimeString(dt=datetime.datetime.now(), lang="en"):
    """Gets the time written out in the specified language.
    
    Keyword Arguments:
    dt -- datetime.datetime, containing time to be written out (REQUIRED)
    lang -- string, two-letter code for language to use (default = "en")
    
    See jjtimestring.languages for list of supported languages"""
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
                timestring = GetNumberString(dt.minute) + " Past " + GetHourString(h)
            elif r == 1 and dt.minute % 15 == 0:
                # type 1: o'clock, quarter past, half past, quarter to
                if dt.minute == 0:
                    timestring = GetNumberString(h, lang) + " O'Clock"
                elif dt.minute == 15:
                    timestring = "Quarter Past " + GetHourString(h, "en").title()
                elif dt.minute == 30:
                    timestring = "Half Past " + GetHourString(h).title()
                elif dt.minute == 45:
                    timestring = "Quarter To " + GetHourString(h1).title()
            elif r == 2 and dt.minute > 9:
                # type 2: "hhh mmm"
                timestring = GetNumberString(h) + " " + GetNumberString(dt.minute)
            elif r == 3 and dt.minute >= 35:
                # type 4: "mmm [Minutes ]To hhh"
                r2 = random.randint(0,1)
                if r2 == 1:
                    midtext = " Minutes To "
                else:
                    midtext = " To "
                timestring = GetNumberString(60-dt.minute).title() + midtext + GetHourString(dt.hour + 1).title()
            elif r == 4:
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
                    timestring = "Half " + GetHourString(h).title()
    elif lang=="en_mil":
      # type 3: military
      if dt.hour < 10:
          timestring = "Zero "
      timestring += GetNumberString(dt.hour).title()
      if dt.minute == 0:
          timestring += " Hundred"
      else:
          if dt.minute < 10:
              timestring += " Zero"
          timestring += " " + GetNumberString(dt.minute).title()
      # randomly determine if we're in the army or navy
      r2 = random.randint(0,1)
      if r2 == 1:
          timestring += " Hours"
    elif lang=="en_idiomatic":
      if dt.minute <= 5:
        timestring = "It's " + GetHourString(h) + "-ish"
      elif dt.minute <= 10:
        timestring = "It's a tad after " + GetHourString(h)
      elif dt.minute <= 20:
        timestring = "It's a fair bit after " + GetHourString(h)
      elif dt.minute < 30:
        timestring = "It's nearly half " + GetHourString(h)
      elif dt.minute == 30:
        timestring = "It's Half " + GetHourString(h).title()
      elif dt.minute <= 40:
        timestring = "It's a touch after half past " + GetHourString(h)
      elif dt.minute <= 55:
        timestring = "It's banging on towards " + GetHourString(h1)
      else:
        timestring = "It's a smidge before " + GetHourString(h1)

    elif lang=="en_oz":
      r2 = random.randint(0,9) # 20% profanity
      profanity = ""
      if r2 == 0:
          profanity = "bloody "
      elif r2 == 1:
          profanity = "farkin "
      if dt.minute <= 5:
        r2 = random.randint(0,9) # profanity 10%
        if r2 == 0:
          timestring = "It's a bee's dick past " + profanity + GetHourString(h)
        else:
          timestring = "It's a bee's whisker past " + profanity + GetHourString(h)
      elif dt.minute <= 10:
        timestring = "It's a " + profanity + "tenner or so past " + GetHourString(h)
      elif dt.minute <= 20:
        timestring = "It's a fair " + profanity + "wack after " + GetHourString(h)
      elif dt.minute < 30:
        r2 = random.randint(0,1)
        if r2 == 0:
          timestring = "Hold ya " + profanity + "horses it's nearly half past " + GetHourString(h)
        else:
          timestring = "It's cooee of half past " + profanity + GetHourString(h)
      elif dt.minute == 30:
        timestring = "It's bang on half past " + profanity + GetHourString(h)
      elif dt.minute <= 40:
        timestring = "It's a blouse after half past " + profanity + GetHourString(h)
      elif dt.minute <= 55:
        timestring = "Hang on a tick and it'll be " + profanity + GetHourString(h1)
        if dt.hour == 23 and random.randint(0,1) == 0: # 50% chance of harold holt
            timestring = "Today's about to chuck a " + profanity +  "Harold"
      else:
        timestring = "It's a smidge before " + profanity + GetHourString(h1)
      if random.randint(0,2) == 0: # 1/3 of the time stick in 'o'clock'
          timestring += " o'clock"
      if dt.hour <= 3:
        timestring += " sparrow's fart"
      elif dt.hour <= 12:
        timestring += " in the morning"
      elif dt.hour <= 16:
        timestring += " in the arvo"
      elif dt.hour <= 20:
        timestring += " in the evening"
      else:
        timestring += " at night"
      r2 = random.randint(0,19) #10% bunch of guff
      if r2 == 0:
          timestring += " and she's apples"
      elif r2 == 1:
          timestring += " and she'll be right"
       
    elif lang=="de":
        # Deutsche, mein Kommandant
        timestring = "Es ist "
        while timestring == "Es ist ":
            r2 = random.randint(0,4)
            if r2 == 0:
                # "Es ist funfzehn Uhr[ zwei]" ** 24H **
                timestring += GetNumberString(dt.hour, "de").title() + " Uhr"
                if dt.minute > 0:
                    timestring += " " + GetNumberString(dt.minute, "de").title()
            elif r2 == 1 and dt.minute % 15 == 0:
                # "Es ist [viertel nach / halb / viertel vor] zwei"
                if dt.minute == 0:
                    timestring += "um " + GetNumberString(dt.hour, "de").title()
                elif dt.minute == 15:
                    timestring += "Viertel nach " + GetHourString(dt.hour, "de", "12h").title()
                elif dt.minute == 30:
                    timestring += "halb " + GetNumberString(h1, "de").title()
                elif dt.minute == 45:
                    timestring += "Viertel vor " + GetHourString(dt.hour+1, "de", "12h").title()
                elif dt.minute >= 25 and dt.minute < 30:
                    # zwei vor halb seiben
                    timestring += GetNumberString(30-dt.minute, "de") + " vor halb " + GetNumberString(h1, "de").title()
                elif dt.minute <= 35 and dt.minute > 30:
                    timestring += GetNumberString(dt.minute-30, "de") + " nach halb " + GetNumberString(h1, "de").title()   
            elif r2 == 2 and dt.minute > 0:
                # "Es ist zwei nach elf
                r3 = random.randint(0,1)
                if r3 == 1 or dt.hour == 12 or dt.hour == 0:
                    timestring += GetNumberString(dt.minute, "de") + " nach " + GetHourString(dt.hour, "de", "12h").title()
            elif r2 == 3 and dt.minute > 30:
                # "Es ist funfundzwanzig vor ein
                r3 = random.randint(0,1)
                if r3 == 1 or dt.hour == 12 or dt.hour == 0:
                    timestring += GetNumberString(60-dt.minute, "de") + " vor " + GetHourString(dt.hour+1, "de", "12h").title()
            elif r2 == 4:
                # Kurz vor halb acht
                if dt.minute < 5:
                    timestring += "Kurz nach um " + GetHourString(dt.hour, "de", "12h").title()
                elif dt.minute > 25 and dt.minute < 30:
                    timestring += "Kurz vor halb " + GetNumberString(h1, "de").title()
                elif dt.minute > 30 and dt.minute < 35:
                    timestring += "Kurz nach halb " + GetNumberString(h1, "de").title()
                elif dt.minute > 55:
                    timestring += "Kurz vor um " + GetNumberString(h1, "de").title()
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
            timestring += GetNumberString(60-dt.minute, "fr") + " moins " + GetNumberString(h1, "fr")
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