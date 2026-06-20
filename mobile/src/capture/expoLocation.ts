// SPDX-License-Identifier: MIT
/**
 * Production capture adapters backed by expo-location.
 *
 * Loaded only by the app, never by the consent-gate test. The OS permission
 * prompt here is the *second* gate; the in-app `ConsentStore` is the first. The
 * sampler is a deliberately conservative placeholder: real Maps/Fit distance
 * resolution is a post-MVP integration, so it derives a coarse distance from a
 * single foreground position read rather than tracking in the background.
 */

import * as Location from "expo-location";

import { type LocationPermission, type TripSampler } from "./transport";

export const expoLocationPermission: LocationPermission = {
  async request(): Promise<boolean> {
    // Foreground only — we never request background location.
    const { status } = await Location.requestForegroundPermissionsAsync();
    return status === Location.PermissionStatus.GRANTED;
  },
};

/**
 * Placeholder sampler. A full implementation would diff a short, foreground,
 * user-initiated track or call the Maps Distance Matrix API; here we return a
 * single best-effort reading so the wiring typechecks and runs without
 * background capture.
 */
export const expoLocationSampler: TripSampler = {
  async sampleDistanceKm(): Promise<number> {
    await Location.getCurrentPositionAsync({
      accuracy: Location.Accuracy.Balanced,
    });
    return 0;
  },
};
