# JJClock
 
A clock for JJ.

_Envisaged to display the time in the form of the front page of a newspaper._

![Image of the original JJ Clock](https://github.com/grob6000/JJClock/raw/main/githubimage.png)

## Main Features:
- With an extensible rendering engine, for clock 'faces' to be added and improved over time.
- Clock faces have the full power of python (and connection to the net; mostly) to show time creatively.
- Configurable over wifi, but able to operate without internet.
- Time and timezone synchronised by GPS (without transmitting your whereabouts to the internet, of course!).

## Key Hardware:
- Raspberry Pi Zero W
- E-Paper Display (Waveshare IT8951)
- Raspberry Pi Touchscreen supported (for testing)

## Software:
- OS: Raspbian Lite
- Primary language: Python
- Key libraries and open source components:
  - Pillow (image manipulation): https://pypi.org/project/Pillow/
  - Flask (for the web backend): https://pypi.org/project/Flask/
  - Waitress (serving the flask app): https://pypi.org/project/waitress/
  - Bootstrap (for web interface make look nicey): https://getbootstrap.com/
  - Mustache (for in-browser templating): https://mustache.github.io/
  - PyGame (for testing display cross-platform): https://pypi.org/project/pygame/
  - PyTZ (for timezone management): https://pypi.org/project/pytz/
  - Timezonefinder (gets the timezone from GPS without the net): https://pypi.org/project/timezonefinder/
  - pyowm (for weather): https://pypi.org/project/pyowm/
  - pygithub (for checking for updates): https://github.com/PyGithub/PyGithub
  - IT8951 display driver by GregDMeyer: https://github.com/GregDMeyer/IT8951
  - qrcode (for creating config qr codes): https://pypi.org/project/qrcode/
  - Python FT5406 Multitouch Driver (for tapping on the test rig): https://github.com/pimoroni/python-multitouch
## Documentation
- Full documentation is unlikely - on request; submit an issue...

## Contributing
- Fork, branch & submit a pull request!
