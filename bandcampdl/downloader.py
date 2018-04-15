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

    resp = requests.get(url)
    sel = Selector(text=resp.text)
    album_name = clean(sel.xpath('//h2[@itemprop="name"]/text()').extract_first(''))
    artist = clean(sel.xpath('//span[@itemprop="byArtist"]/a/text()').extract_first(''))
    album_date = datetime.strptime(next(re.finditer('album_release_date: "(.+)"', resp.text)).group(1), '%d %b %Y %H:%M:%S %Z')
    tags = map(clean, sel.xpath('//div[has-class("tralbumData", "tralbum-tags")]/a[has-class("tag") and @itemprop="keywords"]/text()').extract())
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
        if force:
            echo('Warning: Directory "{}" already exists. Used --force: continuing.'.format(album_path))
        else:
            echo('Error: Directory "{}" already exists. Use --force to continue.'.format(album_path), err=True)
            sys.exit(1)
    tracks = json.loads(next(re.finditer('trackinfo: (\[.+\])', resp.text)).group(1))
    for i, track in enumerate(tracks):
        if not track['file']:
            echo('warning: skipping track "{}" - not available to download'.format(track['title']))
            continue
        url = track['file']['mp3-128']
        if not url.startswith('http'):
            url = 'http:' + url
        name = '{:02} - {}.mp3'.format(track["track_num"], clean(track['title']))
        echo('downloading track {}/{}: {}'.format(i+1, len(tracks), name))
        download(url, os.path.join(album_path, name))

    cover = sel.css('#tralbumArt img::attr(src)').extract_first()
    if cover:
        echo('downloading cover.jpg')
        download(cover, os.path.join(album_path, 'cover.jpg'))

if __name__ == '__main__':
    cli()
