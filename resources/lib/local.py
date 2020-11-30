# -*- coding: utf-8 -*-
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui

ADDON = xbmcaddon.Addon()

def load_channel_subs():
    channels = []
    try:
        subs_path = xbmc.translatePath(ADDON.getAddonInfo('profile') + 'channel_subs')
        f = xbmcvfs.File(subs_path, 'r')
        lines = str(f.read())
        f.close()
        for line in lines.split('\n'):
            items = line.split('#')
            if len(items) < 2:
                continue
            channels.append((items[0],items[1]))
    except Exception as e:
        pass
    return channels

def save_channel_subs(channels):
    try:
        subs_path = xbmc.translatePath(ADDON.getAddonInfo('profile') + 'channel_subs')
        f = xbmcvfs.File(subs_path, 'w')
        for (name, claim_id) in channels:
            f.write(name)
            f.write('#')
            f.write(claim_id)
            f.write('\n')
        f.close()
    except Exception as e:
        xbmcgui.Dialog().notification('Save error', str(e), NOTIFICATION_ERROR)

