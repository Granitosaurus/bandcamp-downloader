import json

import click
import requests
import sys
from click import echo
from parsel import Selector
import os
import re
from datetime import datetime

do_dry_run = False
do_force = False

def clean(text):
    text = text.strip()
    text = text.replace(os.sep, '-')
    return text

def download(url, path):
    global do_dry_run
    if do_dry_run:
        return
    r = requests.get(url, stream=True)
    length = int(r.headers['Content-Length'])
    with open(path, 'wb') as f, \
         click.progressbar(length=length) as bar:
        for chunk in r.iter_content(chunk_size=4096):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                bar.update(len(chunk))

@click.command()
@click.argument('url')
@click.option('--force/--no-force', default=False)
@click.option('--dry-run/--no-dry-run', default=False)
@click.help_option('-h', '--help')
def cli(url, force, dry_run):
    """
    Download tracks from bandcamp album url to `<cwd>/<album_name>/` directory
    """
    global do_dry_run
    do_dry_run = dry_run
    global do_force
    do_force = force

    resp = requests.get(url)

    #TODO full discography
    if 'bandcamp.com/album/' in url:
        download_album(resp)
    elif 'bandcamp.com/track/' in url:
        download_track(resp)
    else:
        raise Exception("Unsupported URL")

def download_album(resp):
    sel = Selector(text=resp.text)
    #metadata = json.loads(sel.xpath('/html/head/script[@type="application/ld+json"]/text()').extract_first(''))
    tracks = json.loads(clean(sel.xpath('/html/head/script/@data-tralbum').extract_first()))

    assert tracks['current']['type'] == 'album'

    artist = tracks['artist']
    album_name = tracks['current']['title']
    album_date = datetime.strptime(tracks['album_release_date'], '%d %b %Y %H:%M:%S %Z')

    tags = map(clean, sel.xpath('//div[has-class("tralbumData", "tralbum-tags")]/a[has-class("tag")]/text()').extract())
    if not album_name:
        echo('No album found on: {}'.format(resp.url), err=True)
        return 1
    album_path = os.path.join(os.getcwd(), artist, '{} - {}'.format(album_date.year, album_name))
    echo("""\
Downloading album {album} ({year}) by {artist}
  to: {path}
(tags: {tags})
""".format(artist=artist, year=album_date.year, album=album_name, path=album_path, tags=', '.join(tags)))
    try:
        if not do_dry_run:
            os.makedirs(album_path)
    except FileExistsError:
        if do_force:
            echo('Warning: Directory "{}" already exists. Used --force: continuing.'.format(album_path))
        else:
            echo('Error: Directory "{}" already exists. Use --force to continue.'.format(album_path), err=True)
            sys.exit(1)

    for i, track in enumerate(tracks['trackinfo']):
        if not track['file']:
            echo('warning: skipping track "{}" - not available to download'.format(track['title']))
            continue
        url = track['file']['mp3-128'].replace('-', '/').replace('mp3/128', 'mp3-128') # probable bug parsel decode json in node attribute
        name = '{:02} - {}.mp3'.format(track["track_num"], clean(track['title']))
        echo('downloading track {}/{}: {}'.format(i+1, len(tracks), name))
        download(url, os.path.join(album_path, name))

    cover = sel.xpath('//*[@id="tralbumArt"]/a/@href').extract_first()
    if cover:
        echo('downloading cover.jpg')
        download(cover, os.path.join(album_path, 'cover.jpg'))

def download_track(resp):
    sel = Selector(text=resp.text)
    track_name = clean(sel.xpath('//h2[@itemprop="name"]/text()').extract_first(''))
    artist = clean(sel.xpath('//span[@itemprop="byArtist"]/a/text()').extract_first(''))
    tralbum_data = json.loads(next(re.finditer('current: (.+),', resp.text)).group(1))
    release_date = datetime.strptime(tralbum_data['release_date'], '%d %b %Y %H:%M:%S %Z')
    tags = map(clean, sel.xpath('//div[has-class("tralbumData", "tralbum-tags")]/a[has-class("tag") and @itemprop="keywords"]/text()').extract())
    artist_path = os.path.join(os.getcwd(), artist)
    echo("""\
Downloading track {track} ({year}) by {artist}
  to: {path}
(tags: {tags})
""".format(artist=artist, year=release_date.year, track=track_name, path=artist_path, tags=', '.join(tags)))
    try:
        if not do_dry_run:
            os.makedirs(artist_path)
    except FileExistsError:
        pass
    tracks = json.loads(next(re.finditer('trackinfo: (\[.+\])', resp.text)).group(1))
    track = tracks[0]
    url = track['file']['mp3-128']
    if not url.startswith('http'):
        url = 'http:' + url
    name = '{} - {}'.format(release_date.strftime("%Y-%m-%d"), clean(track['title']))
    echo('downloading track {}'.format(name))
    download(url, os.path.join(artist_path, name + '.mp3'))

    cover = sel.css('#tralbumArt img::attr(src)').extract_first()
    if cover:
        echo('downloading cover.jpg')
        download(cover, os.path.join(artist_path, name + '-cover.jpg'))

if __name__ == '__main__':
    cli()
