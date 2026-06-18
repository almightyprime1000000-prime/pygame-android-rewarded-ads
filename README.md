# Pygame Android Rewarded Ads

Add Unity Rewarded Ads to Pygame games compiled to Android using Buildozer and Pyjnius.
## Buildozer Configuration

A complete working `buildozer.spec` file is included in this repository.

## Before You Start

You must create a Unity Ads account and obtain:

- Game ID
- Rewarded Placement ID

Replace the placeholder values in the example code with your own IDs.

- Copy files into your project
- Add ShowListenerShim.java to correct package path
- Run:
   buildozer android debug

If you already have a project, compare your configuration against the provided spec file and copy the Unity Ads related settings as needed.

## Project Structure

```text
project/
│
├── buildozer.spec
├── unity_ads_android.py
├── main.py
│
└── src/
    └── main/
        └── java/
            └── com/
                └── your_package/
                    └── ShowListenerShim.java
```

## Example

A complete working example is included in:

main.py

## Support The Project

If this repository helped you integrate Unity Ads into your Pygame Android game, or if you'd like to try a fully integrated production example on Google Play, please consider:

*  Starring this repository
*  Sharing it with other developers
*  Downloading and rating **Skiptrace** on Google Play

Play Store: https://play.google.com/store/apps/details?id=com.almightyprime.skiptrace

press coverage: https://www.fixgamingchannel.com/from-a-jackie-chan-movie-to-google-play-the-story-of-skiptrace/

Your support helps me continue creating tutorials and open-source resources for the Pygame Android community.



