# Bandcamp Downloader

Simple minimal bandcamp downloader cli application:

```
Usage: downloader.py [OPTIONS] URL

  Download tracks from bandcamp album url to `<cwd>/<album_name>/` directory

Options:
  --help  Show this message and exit.
```

# install

    pip install git+https://github.com/Granitosaurus/bandcamp-downloader

# example

```
user@~/music
$ bandcamp-dl "https://stonedjesus.bandcamp.com/album/seven-thunders-roar"
downloading album: seven_thunders_roar
to: /home/user/music/seven_thunders_roar
downloading track: stoned_jesus-bright_like_the_morning.mp3
downloading track: stoned_jesus-electric_mistress.mp3
downloading track: stoned_jesus-indian.mp3
downloading track: stoned_jesus-i'm_the_mountain.mp3
downloading track: stoned_jesus-stormy_monday.mp3
downloading cover.jpg
user@~/music
$ ls seven_thunders_roar/
 cover.jpg                                  stoned_jesus-indian.mp3
 stoned_jesus-bright_like_the_morning.mp3  "stoned_jesus-i'm_the_mountain.mp3"
 stoned_jesus-electric_mistress.mp3         stoned_jesus-stormy_monday.mp3
```
