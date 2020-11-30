# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon
from xbmcgui import ListItem, Dialog, NOTIFICATION_ERROR
from xbmcplugin import addDirectoryItem, addDirectoryItems, endOfDirectory, setContent

import routing
import requests
import urllib
import time

from resources.lib.local import *

ADDON = xbmcaddon.Addon()

lbry_api_url = urllib.unquote(ADDON.getSetting('lbry_api_url'))
if lbry_api_url == '':
    raise Exception('Lbry API URL is undefined.')

items_per_page = ADDON.getSettingInt('items_per_page')
nsfw = ADDON.getSettingBool('nsfw')

plugin = routing.Plugin()
ph = plugin.handle
dialog = Dialog()

def call_rpc(method, params={}):
    try:
        xbmc.log('call_rpc: url=' + lbry_api_url + ', method=' + method + ', params=' + str(params))
        result = requests.post(lbry_api_url, json={'method': method, 'params': params})
        result.raise_for_status()
        rjson = result.json()
        if 'error' in rjson:
            raise Exception(rjson['error']['message'])
        return result.json()['result']
    except Exception as e:
        xbmc.log('call_rpc exception:' + str(e))
        raise e

def result_to_video_list(result):
    items = []
    for item in result['items']:
        if item['value_type'] == 'stream' and item['value']['stream_type'] == 'video':
            # nsfw?
            if 'tags' in item['value']:
                if 'mature' in item['value']['tags'] and not nsfw:
                    continue

            li = ListItem(item['value']['title'] if 'title' in item['value'] else item['file_name'] if 'file_name' in item else '')
            if 'thumbnail' in item['value'] and 'url' in item['value']['thumbnail']:
                li.setArt({
                    'thumb': item['value']['thumbnail']['url'],
                    'poster': item['value']['thumbnail']['url'],
                    'fanart': item['value']['thumbnail']['url']
                })

            infoLabels = {}
            menu = []
            plot = ''
            if 'description' in item['value']:
                plot = item['value']['description']
            if 'author' in item['value']:
                infoLabels['writer'] = item['value']['author']
            elif 'channel_name' in item:
                infoLabels['writer'] = item['channel_name']
            if 'timestamp' in item:
                timestamp = time.localtime(item['timestamp'])
                infoLabels['year'] = timestamp.tm_year
                infoLabels['premiered'] = time.strftime('%Y-%m-%d',timestamp)
            if 'video' in item['value'] and 'duration' in item['value']['video']:
                infoLabels['duration'] = str(item['value']['video']['duration'])
            if 'signing_channel' in item and 'name' in item['signing_channel']:
                ch_name = item['signing_channel']['name']
                ch_title = ''
                if 'value' in item['signing_channel'] and 'title' in item['signing_channel']['value']:
                    ch_title = item['signing_channel']['value']['title']

                plot = '[B]' + ch_name + '[/B]\n' + plot

                infoLabels['studio'] = ch_title if ch_title != '' else ch_name

                menu.append((
                    'Follow ' + ch_name, 'RunPlugin(%s)' % plugin.url_for(plugin_follow, name=urllib.quote(item['signing_channel']['name'].encode('utf-8')), claim_id=item['signing_channel']['claim_id'])
                ))
                menu.append((
                    'Go to ' + ch_name, 'Container.Update(%s)' % plugin.url_for(lbry_channel, name=urllib.quote(ch_name.encode('utf-8')), claim_id=item['signing_channel']['claim_id'],page=1)
                ))
                menu.append((
                    'Download', 'RunPlugin(%s)' % plugin.url_for(claim_download, name=urllib.quote(item['normalized_name'].encode('utf-8')), claim_id=item['claim_id'])
                ))

            infoLabels['plot'] = plot
            li.setInfo('video', infoLabels)

            url = plugin.url_for(claim_play, name=urllib.quote(item['normalized_name'].encode('utf-8')), claim_id=item['claim_id'])

            if len(menu) > 0:
                li.addContextMenuItems(menu)

            items.append((url, li))
        else:
            xbmc.log('ignored item, value_type=' + item['value_type'])
            xbmc.log('item name=' + item['name'].encode('utf-8'))

    return items

@plugin.route('/')
def lbry_root():
    addDirectoryItem(ph, plugin.url_for(plugin_follows), ListItem('Followed Channels'), True)
    addDirectoryItem(ph, plugin.url_for(lbry_new, page=1), ListItem('New'), True)
    addDirectoryItem(ph, plugin.url_for(lbry_search), ListItem('Search'), True)
    endOfDirectory(ph)

@plugin.route('/new/<page>')
def lbry_new(page):
    page = int(page)
    query = {'page': page, 'page_size': items_per_page, 'order_by': 'release_time'}
    if not ADDON.getSettingBool('server_filter_disable'):
        query['stream_types'] = ['video']
    try:
        result = call_rpc('claim_search', query)
        items = result_to_video_list(result)
        addDirectoryItems(ph, items, result['page_size'])
        total_pages = int(result['total_pages'])
        if total_pages > 1 and page < total_pages:
            addDirectoryItem(ph, plugin.url_for(lbry_new, page=page+1), ListItem('Next Page'), True)
    except Exception as e:
        dialog.notification('Problem doing claim search', str(e), NOTIFICATION_ERROR)
    endOfDirectory(ph)

@plugin.route('/follows')
def plugin_follows():
    channels = load_channel_subs()
    resolve_uris = []
    for (name,claim_id) in channels:
        resolve_uris.append(name+'#'+claim_id)
    channel_info = call_rpc('resolve', {'urls': resolve_uris})

    for (name,claim_id) in channels:
        uri = name+'#'+claim_id
        li = ListItem(name)
        if not 'error' in channel_info[uri]:
            plot = ''
            if 'title' in channel_info[uri]['value']:
                plot = plot + '[B]%s[/B]\n' % channel_info[uri]['value']['title']
            if 'description' in channel_info[uri]['value']:
                plot = plot + channel_info[uri]['value']['description']
            infoLabels = { 'plot': plot }
            li.setInfo('video', infoLabels)

            if 'thumbnail' in channel_info[uri]['value'] and 'url' in channel_info[uri]['value']['thumbnail']:
                li.setArt({
                    'thumb': channel_info[uri]['value']['thumbnail']['url'],
                    'poster': channel_info[uri]['value']['thumbnail']['url'],
                    'fanart': channel_info[uri]['value']['thumbnail']['url']
                })

        menu = []
        menu.append((
            'Unfollow Channel', 'RunPlugin(%s)' % plugin.url_for(plugin_unfollow, name=urllib.quote(name), claim_id=claim_id)
        ))
        li.addContextMenuItems(menu)
        addDirectoryItem(ph, plugin.url_for(lbry_channel, name=urllib.quote(name), claim_id=claim_id, page=1), li, True)
    endOfDirectory(ph)

@plugin.route('/follows/add/<name>/<claim_id>')
def plugin_follow(name, claim_id):
    name = urllib.unquote(name)
    channels = load_channel_subs()
    channel = (str(name),str(claim_id))
    if not channel in channels:
        channels.append(channel)
    save_channel_subs(channels)

@plugin.route('/follows/del/<name>/<claim_id>')
def plugin_unfollow(name, claim_id):
    name = urllib.unquote(name)
    channels = load_channel_subs()
    channels.remove((str(name),str(claim_id)))
    save_channel_subs(channels)
    xbmc.executebuiltin('Container.Refresh')

@plugin.route('/channel/<name>/<claim_id>')
def lbry_channel_landing(name,claim_id):
    lbry_channel(name,claim_id,1)

@plugin.route('/channel/<name>/<claim_id>/<page>')
def lbry_channel(name,claim_id,page):
    name = urllib.unquote(name)
    page = int(page)
    query = {'page': page, 'page_size': items_per_page, 'order_by': 'release_time', 'channel': name+'#'+claim_id}
    if not ADDON.getSettingBool('server_filter_disable'):
        query['stream_types'] = ['video']
    try:
        result = call_rpc('claim_search', query)
        items = result_to_video_list(result)
        addDirectoryItems(ph, items, result['page_size'])
        total_pages = int(result['total_pages'])
        if total_pages > 1 and page < total_pages:
            addDirectoryItem(ph, plugin.url_for(lbry_channel, name=urllib.quote(name), claim_id=claim_id, page=page+1), ListItem('Next Page'), True)
    except Exception as e:
        dialog.notification('Problem doing claim search', str(e), NOTIFICATION_ERROR)
    endOfDirectory(ph)

@plugin.route('/search')
def lbry_search():
    query = dialog.input('Enter search terms')
    lbry_search_pager(urllib.quote_plus(query), 1)

@plugin.route('/search/<query>/<page>')
def lbry_search_pager(query, page):
    query = urllib.unquote_plus(query)
    xbmc.log('q=' + query + ' p=' + str(page))
    page = int(page)
    if query != '':
        params = {'text': query, 'page': page, 'page_size': items_per_page}
        #if not ADDON.getSettingBool('server_filter_disable'):
        #    params['stream_types'] = ['video']
        result = call_rpc('claim_search', params)
        items = result_to_video_list(result)
        addDirectoryItems(ph, items, result['page_size'])
        total_pages = int(result['total_pages'])
        if total_pages > 1 and page < total_pages:
            addDirectoryItem(ph, plugin.url_for(lbry_search_pager, query=urllib.quote_plus(query), page=page+1), ListItem('Next Page'), True)
        endOfDirectory(ph)
    else:
        endOfDirectory(ph, False)

@plugin.route('/play/<name>/<claim_id>')
def claim_play(name, claim_id):
    uri = urllib.unquote(name) + '#' + claim_id

    claim_info = call_rpc('resolve', {'urls': uri})
    if 'error' in claim_info[uri]:
        dialog.notification('error in claim info uri', claim_info[uri]['error']['name'], NOTIFICATION_ERROR)
        return

    if 'fee' in claim_info[uri]['value']:
        dialog.notification('Payment required', 'Video is not free, and payment is not implemented yet', NOTIFICATION_ERROR)
        return

    result = call_rpc('get', {'uri': uri, 'save_file': False})
    xbmc.Player().play(result['streaming_url'].replace('0.0.0.0','127.0.0.1'))

@plugin.route('/download/<name>/<claim_id>')
def claim_download(name, claim_id):
    uri = urllib.unquote(name) + '#' + claim_id

    claim_info = call_rpc('resolve', {'urls': uri})
    if 'error' in claim_info[uri]:
        dialog.notification('error in claim info uri', claim_info[uri]['error']['name'], NOTIFICATION_ERROR)
        return

    if 'fee' in claim_info[uri]['value']:
        dialog.notification('Payment required', 'Video is not free, and payment is not implemented yet', NOTIFICATION_ERROR)
        return

    result = call_rpc('get', {'uri': uri, 'save_file': True})

def run():
    plugin.run()
