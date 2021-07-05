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
- Raspberry Pi
- E-Paper Display (Waveshare IT8951)

## Software:
- OS: Raspbian Lite
- Primary language: Python
- Key libraries and open source components:
  - Bootstrap (for web interface)
  - PyGame (for testing display)
  - PyTZ (for timezone management)
  - pyowm (for weather)
  - pygithub (for updates / connecting to this repository)

## Documentation
- Full documentation is unlikely - on request; submit an issue.

## Contributing
- Fork, branch & submit a pull request!
  - Welcome new renderers
  - Welcome improvements to the config interface, for potential use on your other projects!
