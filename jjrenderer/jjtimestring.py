import datetime
import logging
import random

## LANGUAGE NUMBER ELEMENTS ##

numberstrings_en = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
decadestrings_en = ["Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
monthstrings_en = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
daystrings_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

numberstrings_de = ["null", "ein", "zwei", "drei", "vier", "funf", "sechs", "sieben", "acht", "neun", "zehn", "elf", "zwölf", "dreizehn", "vierzehn", "funfzehn", "sechzehn", "siebzehn", "achtzehn", "neunzehn"]
decadestrings_de = ["zwanzig", "dreizig", "vierzig", "funfzig", "sechzig", "siebzig", "achtzig", "neunzig"]

numberstrings_es = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce", "trece", "catorce", "quince", "dieceséis", "diecisiete", "dieciocho", "diecinueve", "viente", "vientiuno", "vientidós", "vientitrés", "vienticuatro", "vienticinco", "vientiséis", "vientisiete", "vientiocho", "vientinueve"]
decadestrings_es = ["viente", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]

numberstrings_fr = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
decadestrings_fr = ["vingt", "trente", "quarante", "cinguante"]
monthstrings_fr = ["janvier", "février", "mars", "avril", "mai", "juin", "juilliet", "août", "septembre", "octobre", "novembre", "décembre"]
daystrings_fr = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

numberstrings_it = ["?", "uno", "due", "tre", "quattro", "cinque", "sei", "sette", "otto", "nove", "dieci", "undici", "dodici", "tredici", "quattordici", "quindici", "sedici", "diciassette", "diciotto", "diciannove"]
decadestrings_it = ["venti", "trenta", "quaranta", "cinquanta", "sesanta", "settanta", "ottanta", "novanta"]

numberstrings_et = ["null", "üks", "kaks", "kolm", "neli", "viis", "kuus", "seitse", "kaheksa", "üheksa", "kümme", "üksteist", "kaksteist", "kolmteist", "neliteist", "viisteist", "kussteist", "seitseteist", "kaheksateist", "üheksateist"]
decadestrings_et = ["kakskümmend", "kolmkümmend", "nelikümmend", "viiskümmend", "kuuskümmend", "seitsekümmend", "kaheksakümmend" "üheksakümmend"]

def HalfAndHalf(sentence):
  sentence = str(sentence)
  imin = len(sentence)
  for i in range(0,len(sentence)):
    if sentence[i] == " ":
      if abs(i - len(sentence)/2) < abs(imin-len(sentence)/2):
        imin = i
  r = [sentence[:imin],sentence[imin+1:]]
  logging.debug("halfandhalf: " + str(r))
  return r
      

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
    if lang == "fr":
      monthstrings = monthstrings_fr
      daystrings = daystrings_fr
    else:
      monthstrings = monthstrings_en
      daystrings = daystrings_en
    if lang == "fr":
      return "{0}, {1} {2} {3}".format(daystrings[dt.weekday()], dt.day, monthstrings[dt.month - 1], dt.year)
    else: # en
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
                    timestring = "Half " + GetHourString(h)
    elif lang=="en_idiomatic":
      if dt.minute <= 5:
        timestring = "It's " + GetHourString(h) + "-ish"
      elif dt.minute <= 10:
        timestring = "It's a tad after " + GetHourString(h)
      elif dt.minute <= 20:
        timestring = "It's a fair bit after " + GetHourString(h)
      elif dt.minute < 30:
        timestring = "It's Nearly half " + GetHourString(h)
      elif dt.minute == 30:
        timestring = "It's Half " + GetHourString(h)
      elif dt.minute <= 40:
        timestring = "It's a touch after half past " + GetHourString(h)
      elif dt.minute <= 55:
        timestring = "It's banging on towards " + GetHourString(h1)
      else:
        timestring = "It's a smidge before " + GetHourString(h1)
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