# ============================================================
# unity_ads_android.py
# Author: Wonder Kofi Junior (Almighty Prime)
# Project: adsexample (com.almightyprime.adsexample)
#
# PURPOSE:
#   This module integrates Unity Rewarded Ads into a Python/Pygame
#   Android game using Pyjnius (pyjnius bridges Python and Java on Android).
#
# HOW IT WORKS (overview):
#   1. I grab a reference to the Android Activity (the running app window)
#   2. I use Pyjnius to call Unity Ads Java SDK methods from Python
#   3. A Java "shim" class (ShowListenerShim.java) handles ad callbacks
#      because Pyjnius cannot reliably implement certain Java interfaces
#   4. Python polls the shim's static flags to know when an ad completed
#
# DEPENDENCIES:
#   - pyjnius (pip install pyjnius) — bridges Python <-> Java on Android
#   - Unity Ads SDK (added as a .aar in your Android build)
#   - ShowListenerShim.java (must be compiled into the Android APK)
#   - Buildozer or similar tool to compile the Android APK
# ============================================================

from jnius import autoclass, cast, PythonJavaClass, java_method
import threading
import time

# ============================================================
# STEP 1 — Get the Android Activity
# The Activity is the Android equivalent of the "app window".
# Unity Ads needs it to display ads on screen.
# I try SDLActivity first (used by Pygame/SDL builds),
# then fall back to PythonActivity (used by Kivy builds).
# ============================================================
activity = None
try:
    SDLActivity = autoclass('org.libsdl.app.SDLActivity')
    activity = cast('android.app.Activity', SDLActivity.mSingleton)
    print(">>> UnityAds Wrapper: Using SDLActivity")
except Exception as e:
    print(">>> UnityAds Wrapper: SDLActivity unavailable:", e)
    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        print(">>> UnityAds Wrapper: Using PythonActivity")
    except Exception as e2:
        print(">>> UnityAds Wrapper: No Activity available:", e2)

# ============================================================
# STEP 2 — Load Unity Ads Java classes via Pyjnius
# autoclass() lets us use Java classes directly in Python.
# These classes come from the Unity Ads SDK (.aar file).
# ============================================================
UnityAds = autoclass("com.unity3d.ads.UnityAds")
UnityAdsLoadOptions = autoclass("com.unity3d.ads.UnityAdsLoadOptions")
UnityAdsShowOptions = autoclass("com.unity3d.ads.UnityAdsShowOptions")

# ShowListenerShim is The custom Java class (see ShowListenerShim.java).
# It listens for ad events (completed, skipped, failed) and stores
# the result in static boolean flags that Python can read later.
ShowListenerShim = autoclass("com.almightyprime.adsexample.ShowListenerShim")

# ============================================================
# STEP 3 — Runnable helper
# Android requires UI operations (like showing ads) to run on
# the "UI thread". PyRunnable wraps a Python function so it
# can be passed to Android's runOnUiThread() method.
# ============================================================
class PyRunnable(PythonJavaClass):
    __javainterfaces__ = ['java.lang.Runnable']
    __javacontext__ = 'app'

    def __init__(self, func):
        super().__init__()
        self.func = func

    @java_method("()V")
    def run(self):
        try:
            self.func()
        except Exception as e:
            print("UI Runnable error:", e)

def run_on_ui_thread(func):
    """Run a Python function on Android's main UI thread."""
    if activity is None:
        print("Unity Ads: WARNING - Activity is None; cannot run on UI thread")
        return
    try:
        activity.runOnUiThread(PyRunnable(func))
    except Exception as e:
        print("Unity Ads: runOnUiThread failed:", e)

# ============================================================
# STEP 4 — Internal state tracking
# These variables track whether Unity Ads is ready to show an ad.
# state_lock prevents race conditions between threads.
# ============================================================
state_lock = threading.Lock()
ads_initialized = False   # True once Unity Ads SDK is ready
ad_ready = False          # True once an ad has been loaded and is ready to show
pending_show = False      # True if show was called before the ad finished loading
global_ad_unit_id = None  # Stores the ad unit ID for retry/reload use

# ============================================================
# STEP 5 — Unity Ads Listeners (Python side)
# These classes implement Java interfaces so Unity Ads SDK
# can notify us when initialization or loading finishes.
# NOTE: The "show" listener is handled by ShowListenerShim.java
# instead because Pyjnius has issues with that specific interface.
# ============================================================

class InitListener(PythonJavaClass):
    """Called by Unity Ads SDK when initialization succeeds or fails."""
    __javainterfaces__ = ["com.unity3d.ads.IUnityAdsInitializationListener"]
    __javacontext__ = "app"

    @java_method("()V")
    def onInitializationComplete(self):
        global ads_initialized
        with state_lock:
            ads_initialized = True
        print("Unity Ads: INITIALIZED")
        # Auto-load an ad as soon as the SDK is ready
        if global_ad_unit_id:
            load_rewarded(global_ad_unit_id)

    @java_method("(Lcom/unity3d/ads/UnityAds$UnityAdsInitializationError;Ljava/lang/String;)V")
    def onInitializationFailed(self, err, msg):
        err_str = err.toString() if err else "Unknown"
        print(f"Unity Ads: INIT FAIL - {err_str}: {msg}")

class LoadListener(PythonJavaClass):
    """Called by Unity Ads SDK when an ad finishes loading or fails to load."""
    __javainterfaces__ = ["com.unity3d.ads.IUnityAdsLoadListener"]
    __javacontext__ = "app"

    @java_method("(Ljava/lang/String;)V")
    def onUnityAdsAdLoaded(self, placementId):
        global ad_ready, pending_show
        with state_lock:
            ad_ready = True
            queued = pending_show  # Was show() called while we were loading?
            pending_show = False
        print("Unity Ads: AD LOADED", placementId)
        # If the game already requested to show an ad, show it now
        if queued:
            threading.Thread(target=lambda: show_rewarded(placementId), daemon=True).start()

    @java_method("(Ljava/lang/String;Lcom/unity3d/ads/UnityAds$UnityAdsLoadError;Ljava/lang/String;)V")
    def onUnityAdsFailedToLoad(self, placementId, err, msg):
        err_str = err.toString() if err else "Unknown"
        print(f"Unity Ads: LOAD FAIL {placementId} - {err_str}: {msg}")
        # Automatically retry loading after 2 seconds
        def retry():
            time.sleep(2.0)
            load_rewarded(placementId)
        threading.Thread(target=retry, daemon=True).start()

# Instantiate listeners (must be kept alive as variables, not garbage collected)
init_listener = InitListener()
load_listener = LoadListener()
show_listener = ShowListenerShim()  # Java shim handles show callbacks

# ============================================================
# STEP 6 — Public API
# These are the functions your game code calls directly.
# ============================================================

def initialize_unity_ads(game_id, test_mode=True):
    """
    Initialize the Unity Ads SDK.
    - game_id: Your Unity game ID (found in Unity dashboard)
    - test_mode: Set True during development, False for production
    Call this once when your game starts.
    """
    print("Unity Ads: INITIALIZING…")
    if activity is None:
        print("Unity Ads: ERROR - Activity is None; cannot initialize")
        return
    with state_lock:
        initialized = ads_initialized
    if initialized:
        print("Unity Ads: Already initialized")
        return
    try:
        run_on_ui_thread(lambda: UnityAds.initialize(activity, game_id, test_mode, init_listener))
    except Exception as e:
        print("Unity Ads: initialize failed:", e)

def load_rewarded(ad_unit_id="Rewarded_Android"):
    """
    Pre-load a rewarded ad so it's ready to show instantly when needed.
    - ad_unit_id: Your placement ID from the Unity dashboard (default: "Rewarded_Android")
    Call this after initialize_unity_ads(), and again after each ad is shown.
    """
    global global_ad_unit_id
    global_ad_unit_id = ad_unit_id
    with state_lock:
        initialized = ads_initialized
    if not initialized:
        print("Unity Ads: WAIT INIT")
        return
    print("Unity Ads: LOADING…", ad_unit_id)
    try:
        run_on_ui_thread(lambda: UnityAds.load(ad_unit_id, UnityAdsLoadOptions(), load_listener))
    except Exception as e:
        print("Unity Ads: load failed:", e)

def show_rewarded(ad_unit_id="Rewarded_Android"):
    """
    Show the rewarded ad to the player.
    - If the ad is already loaded, it shows immediately.
    - If not loaded yet, it queues the show and displays as soon as loading finishes.
    After the ad, call get_reward() to check the result.
    """
    global ad_ready, pending_show
    with state_lock:
        if ad_ready:
            ad_ready = False
            queued = False
        else:
            # Ad not ready yet — queue the show request
            queued = True
            pending_show = True
    if queued:
        print("Unity Ads: QUEUE SHOW")
        load_rewarded(ad_unit_id)
        return
    print("Unity Ads: SHOW - Preparing for ad display", ad_unit_id)
    opts = UnityAdsShowOptions()
    try:
        run_on_ui_thread(lambda: UnityAds.show(activity, ad_unit_id, opts, show_listener))
    except Exception as e:
        print("Unity Ads: show failed:", e)
        load_rewarded(ad_unit_id)  # Reload for next attempt

def get_reward():
    """
    Check whether the player earned a reward from the last ad.
    Call this each game loop frame after showing an ad.

    Returns:
      "rewarded" — player watched the full ad, give them the reward
      "skipped"  — player closed the ad early, no reward
      "failed"   — ad failed to show, no reward
      None       — ad hasn't finished yet, keep waiting
    """
    if ShowListenerShim.completed:
        ShowListenerShim.completed = False
        return "rewarded"
    elif ShowListenerShim.skipped:
        ShowListenerShim.skipped = False
        return "skipped"
    elif ShowListenerShim.failed:
        ShowListenerShim.failed = False
        return "failed"
    return None

def start_unity_ads(game_id, ad_unit_id="Rewarded_Android", test_mode=True):
    """
    Convenience function: initializes Unity Ads AND pre-loads the first ad.
    This is the recommended single call to put in your game's startup code.

    Example usage:
        start_unity_ads("your_unity_game_id", test_mode=False)
    """
    initialize_unity_ads(game_id, test_mode=test_mode)
    def _preload():
        time.sleep(0.3)  # Short delay to let initialization settle
        load_rewarded(ad_unit_id)
    threading.Thread(target=_preload, daemon=True).start()



