# minicloze Capacitor (Android)

Native Android shell for the minicloze static PWA.
Capacitor with bundled web assets and stronger offline (not TWA).
Vercel deploy of minicloze-web/static is unchanged.

## Requirements

- Node.js 18+
- Android Studio with SDK 35
- JDK 17+

## Quick start

```
cd capacitor
npm install
npm run cap:sync
npm run cap:open
```

Custom static source:

```
STATIC_SRC=/path/to/minicloze-web/static npm run cap:sync
```

## What cap:sync does

1. scripts/sync-www.sh copies minicloze-web/static (including data/) into www/.
2. scripts/patch-capacitor-offline.sh applies Capacitor offline tweaks:
   - Cache name minicloze-capacitor-v1
   - Precaches every /data/*.json in the service worker APP_SHELL
   - Registers the SW at /service-worker.js with scope / (https://localhost origin)
3. npx cap sync android copies www/ into android/app/src/main/assets/public/.

www/ and android/app/src/main/assets/public/ are gitignored — always run sync before building.

## Capacitor config

- appId: com.ybj14.minicloze
- appName: minicloze
- webDir: www
- server.androidScheme: https
- server.hostname: localhost

WebView origin is https://localhost so absolute PWA paths and the service worker work.
Docs: https://capacitorjs.com/docs/guides/spa

Android enables cleartext + localhost-friendly network security config for debugging.

## Build APK / AAB (Android Studio)

1. Run `npm run cap:sync` in this directory.
2. Open the project: `npm run cap:open` (or File → Open → capacitor/android).
3. Wait for Gradle sync to finish.
4. Debug APK: Build → Build Bundle(s) / APK(s) → Build APK(s).
   Output: android/app/build/outputs/apk/debug/app-debug.apk
5. Release AAB: Build → Generate Signed Bundle / APK → follow the wizard.

CLI when SDK is installed:

```
cd android
./gradlew assembleDebug
./gradlew bundleRelease
```

## Offline approach

- Bundled assets: full static shell + course JSON copied into the APK via cap sync
- Service worker: same network-first / SWR logic as the web PWA, plus precache of all /data/*.json
- Origin: https://localhost so / paths and SW registration match the web app

## Repo layout

```
capacitor/
  package.json
  capacitor.config.json
  scripts/sync-www.sh
  scripts/patch-capacitor-offline.sh
  android/
  www/          # generated, gitignored
  README.md
```

## Notes

- This environment may not have the Android SDK; build APKs with Android Studio on your machine.
- Do not deploy capacitor/ via Vercel — keep vercel.json pointed at minicloze-web/static only.

