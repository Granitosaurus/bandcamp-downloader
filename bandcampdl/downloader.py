import json

import click
import requests
import sys
from click import echo
from parsel import Selector
import os
import re


def clean(text):
    text = text.replace(os.sep, '')
    text = text.lower().strip().replace(' ', '_')
    text = re.sub('_{2,}', '_', text)
    text = text.replace('_-_', '-')
    return text


@click.command()
@click.argument('url')
def cli(url):
    """
    Download tracks from bandcamp album url to `<cwd>/<album_name>/` directory
    """
    resp = requests.get(url)
    sel = Selector(text=resp.text)
    album_name = clean(sel.xpath('//h2[@itemprop="name"]/text()').extract_first(''))
    artist = clean(sel.xpath('//span[@itemprop="byArtist"]/a/text()').extract_first(''))
    if not album_name:
        echo('no album found on: {}'.format(resp.url), err=True)
        return 1
    album_path = os.path.join(os.getcwd(), album_name)
    echo('downloading album: {}\nto: {}'.format(album_name, album_path))
    try:
        os.mkdir(album_path)
    except FileExistsError:
        print('Error: Directory "{}" already exists'.format(album_path))
        sys.exit()
    tracks = json.loads(re.findall('trackinfo: (\[.+\])', resp.text)[0])
    for track in tracks:
        url = track['file']['mp3-128']
        if not url.startswith('http'):
            url = 'http:' + url
        name = '{}-{}.mp3'.format(artist, clean(track['title']))
        echo('downloading track: {}'.format(name))
        with open(os.path.join(album_path, name), 'wb') as f:
            f.write(requests.get(url).content)
    cover = sel.css('#tralbumArt img::attr(src)').extract_first()
    if cover:
        echo('downloading cover.jpg')
        with open(os.path.join(album_path, 'cover.jpg'), 'wb') as f:
            f.write(requests.get(cover).content)

if __name__ == '__main__':
    cli()
