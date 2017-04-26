import json

import click
import re
import requests
from click import echo
from parsel import Selector
import os


def clean(text):
    return text.lower().strip().replace(' ', '_')


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
    os.mkdir(album_path)
    tracks = json.loads(re.findall('trackinfo: (\[.+\])', resp.text)[0])
    for track in tracks:
        url = 'http:{}'.format(track['file']['mp3-128'])
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
