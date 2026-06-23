# Unity Rewarded Ads in Python/Pygame (Android)
### A real-world implementation by Wonder Kofi Junior (AlmightyPrime)
### From the game: Skiptrace — https://play.google.com/store/apps/details?id=com.almightyprime.skiptrace

---

## What this package contains

This is the complete, working implementation of Unity Rewarded Ads inside a Python/Pygame Android game. Every file here is extracted from Skiptrace — a real game live on the Google Play Store. This is not a proof of concept. It runs in production.

```
skiptrace_ads_tutorial/
│
├── python/
│   └── unity_ads_android.py     ← The main Python wrapper (copy into your project)
│
├── java/
│   └── ShowListenerShim.java    ← Custom Java listener (compile into your APK)
│
├── buildozer/
│   └── buildozer.spec           ← Full buildozer config with [ADS RELEVANT] markers
│
└── example_usage/
    └── example_usage.py         ← How to wire it into your game loop
```

---

## Why a Java shim is needed

Pyjnius (the Python-Java bridge used in Buildozer/p4a projects) cannot reliably implement the `IUnityAdsShowListener` interface in Python. Callbacks fire on Android's UI thread at unpredictable times, causing crashes or silent failures.

The fix: implement the listener in pure Java (`ShowListenerShim.java`), store results as static boolean flags, and poll them safely from Python each frame using `get_reward()`.

---

## Quick start (3 steps)

### 1. Copy the Python file
Place `unity_ads_android.py` in your project root (same folder as `main.py`).

### 2. Add the Java shim
Place `ShowListenerShim.java` in:
```
your_project/src/main/java/com/yourpackage/yourapp/ShowListenerShim.java
```
Update the `package` line at the top to match your own package name.

Then in `buildozer.spec`, add:
```
android.add_src = src/main/java
```

### 3. Add the Gradle dependency
In `buildozer.spec`:
```
android.gradle_dependencies = com.unity3d.ads:unity-ads:4.12.2
android.gradle_repositories = "https://maven.google.com/", "https://unity3d.jfrog.io/artifactory/unity-ads"
android.enable_multidex = True
```
MultiDex is required — Unity Ads pushes the method count over Android's 64K limit.

---

## Using it in your game

```python
import unity_ads_android as ads

# At startup (once)
ads.start_unity_ads(game_id="YOUR_UNITY_GAME_ID", test_mode=False)

# When player clicks "Watch Ad"
ads.show_rewarded("Rewarded_Android")

# Every frame in your game loop
reward = ads.get_reward()
if reward == "rewarded":
    # Give the player their reward
elif reward == "skipped":
    # No reward
elif reward == "failed":
    # Ad failed — handle gracefully
```

See `example_usage/example_usage.py` for the full pattern including state tracking and timeout handling.

---

## Important notes

- Set `test_mode=True` while developing, `False` before publishing
- Your Unity Game ID comes from: Unity Dashboard → Monetization → Get Started
- The placement ID `"Rewarded_Android"` must match what you set in the Unity dashboard
- In `buildozer.spec`, set `android.meta_data = com.unity3d.ads.metadata.testmode=False` for production builds

---

## About this implementation

Built by **Wonder Kofi Junior** (AlmightyPrime), a solo developer from Ghana.
Two years of learning, failing, and finishing.


## Support The Project

If this repository helped you integrate Unity Ads into your Pygame Android game, or if you'd like to try a fully integrated production example on Google Play, please consider:

*  Starring this repository
*  Sharing it with other developers
*  Downloading and rating **Skiptrace** on Google Play

Play Store: https://play.google.com/store/apps/details?id=com.almightyprime.skiptrace

Developer story: https://www.fixgamingchannel.com/from-a-jackie-chan-movie-to-google-play-the-story-of-skiptrace/

Your support helps me continue creating tutorials and open-source resources for the Pygame Android community.






