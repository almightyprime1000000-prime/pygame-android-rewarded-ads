// ============================================================
// ShowListenerShim.java
// Author: Wonder Kofi Junior (Almighty Prime)
// Project: adsexample (com.almightyprime.adsexample)
//
// PURPOSE:
//   This Java class listens for Unity Ads "show" events and stores
//   the result in simple static boolean flags that Python can read.
//
// WHY THIS EXISTS:
//   Pyjnius (the Python-Java bridge used in this project) cannot
//   reliably implement the IUnityAdsShowListener interface directly
//   in Python. The show listener involves callbacks that fire on
//   Android's UI thread at unpredictable times, which causes Pyjnius
//   to crash or silently fail.
//
//   The solution: implement the listener in pure Java, store the
//   result in static booleans, and let Python poll those flags
//   safely each game loop frame using get_reward() in ads.py.
//
// HOW TO USE:
//   1. Place this file in your Android project's Java source folder:
//      <project>/src/main/java/com/almightyprime/adsexample/
//   2. It is automatically used by unity_ads_android.py — no extra
//      setup needed on the Python side.
// ============================================================

package com.almightyprime.adsexample;

import android.util.Log;
import com.unity3d.ads.IUnityAdsShowListener;
import com.unity3d.ads.UnityAds;

public class ShowListenerShim implements IUnityAdsShowListener {

    // --------------------------------------------------------
    // Static flags — Python reads these via get_reward() in ads.py.
    // Static means they belong to the class, not an instance,
    // so Python can access them directly as ShowListenerShim.completed etc.
    // Only one flag is ever true at a time; Python resets them after reading.
    // --------------------------------------------------------
    public static boolean completed = false;  // Player watched the full ad
    public static boolean skipped = false;    // Player closed the ad early
    public static boolean failed = false;     // Ad failed to display

    // --------------------------------------------------------
    // Called when the ad starts playing on screen.
    // We just log it — no action needed here.
    // --------------------------------------------------------
    @Override
    public void onUnityAdsShowStart(String placementId) {
        Log.i("UnityAdsShim", "Show start: " + placementId);
    }

    // --------------------------------------------------------
    // Called when the player taps/clicks the ad.
    // We just log it — no action needed here.
    // --------------------------------------------------------
    @Override
    public void onUnityAdsShowClick(String placementId) {
        Log.i("UnityAdsShim", "Show click: " + placementId);
    }

    // --------------------------------------------------------
    // Called when the ad finishes (either completed or skipped).
    // We set the appropriate flag so Python can check the result.
    // --------------------------------------------------------
    @Override
    public void onUnityAdsShowComplete(String placementId, UnityAds.UnityAdsShowCompletionState state) {
        Log.i("UnityAdsShim", "Show complete: " + placementId + " " + state);
        if (state == UnityAds.UnityAdsShowCompletionState.COMPLETED) {
            completed = true;  // Full ad watched — player earns reward
        } else {
            skipped = true;    // Ad was skipped/closed early — no reward
        }
    }

    // --------------------------------------------------------
    // Called if the ad fails to display (network issue, no fill, etc.)
    // Sets the failed flag so Python can handle it gracefully.
    // --------------------------------------------------------
    @Override
    public void onUnityAdsShowFailure(String placementId, UnityAds.UnityAdsShowError error, String message) {
        Log.e("UnityAdsShim", "Show failure: " + placementId + " " + error + " " + message);
        failed = true;
    }
}
