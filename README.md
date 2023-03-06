# Kodi/XBMC plugin for LBRY

This is a basic plugin for accessing [LBRY](https://lbry.com) content (video's only, for now).

By default you don't need to install any extra software to start using this LBRY plugin, the plugin uses the API server provided by lbry.tv (https://api.lbry.tv/api/v1/proxy).

Alternatively, you can run your own API server and contribute to the LBRY network by hosting content data of videos you watched. This enables the 'Download' feature in the plugin, so you can watch videos uninterrupted or save the video to a local file. Also this enables wallet features like watching paid videos or tipping authors.

You will need to run `lbrynet` client (installation described here: https://github.com/lbryio/lbry-sdk) and have a bit of storage space available.

## Using
You have to install LBRY app from [lbry.com](https://lbry.com/get) and let it running in background.
In the LBRY KODI addon settings replace public server by http://localhost:5279
It loads faster and all videos play than with public server.
In LBRY app, you have to sign in with your Odysee credentials and select my account in LBRY addon. It will load account but subscription list will stay empty because it is currently not supported but local only.

## See also
* [Odysee Adnroid app](https://f-droid.org/en/packages/com.odysee.floss/)
* [Try LBRY Android app](https://f-droid.org/en/packages/ua.gardenapple.trylbry/)
* https://github.com/lbryio/lbry-fdroid sources of LBRY app for Android
