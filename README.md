# Root Discover

An Android app that lists root apps, modules and tools — with a link to each project's GitHub
repository — plus which phone brands and devices can be rooted.

Data comes from **[Awesome Android Root](https://github.com/awesome-android-root/awesome-android-root)**
(MIT License) and is bundled in the app, so it works offline.

## What's inside

| Tab | Content |
|---|---|
| **Apps** | 735 apps & modules in 16 categories (root managers, LSPosed modules, ad blockers, debloaters, backup, privacy, performance…). Search, filter by category, show ★ featured or GitHub-only entries. Tap to open the repo, long-press to copy the link. Badges show FOSS/Proprietary, Magisk / KernelSU / APatch / LSPosed support, F-Droid and Play Store availability. |
| **Devices** | Bootloader-unlock status for 10 brands (Pixel, OnePlus, Nothing, Motorola, Sony, ASUS, Xiaomi, Samsung, OPPO/Realme/vivo/Honor, Huawei) with a link to each rooting guide; 25 temporary-root projects for locked bootloaders with their exact supported models and firmware; and a "which root solution should I use?" guide. |
| **About** | Stats, safety notes, links to the source repository. |

Requires Android 8.0 (API 26) or newer. Uses Material You colours on Android 12+.

## Get the APK — no Android Studio needed

1. Create a new repository on GitHub and upload everything in this folder (keep the `.github` folder).
2. Open the **Actions** tab. The **Build APK** workflow runs automatically (or press *Run workflow*).
3. When it finishes (about 3–5 minutes), open the run and download **Root-Discover-APK**.
   Unzip it and install `Root-Discover.apk` on your phone (allow "Install unknown apps" when asked).

To publish a release with the APK attached, push a tag: `git tag v1.0.0 && git push --tags`.

The workflow also refreshes the app list from Awesome Android Root every Monday (and on manual runs),
so new builds pick up newly listed apps.

## Build locally

Open the folder in Android Studio (Ladybug or newer) and choose **Build › Build APK(s)**, or run:

```bash
./gradlew assembleRelease        # app/build/outputs/apk/release/app-release.apk
```

The release build is signed with the debug key so it installs directly. Before publishing to a store,
create your own keystore and set it in `app/build.gradle.kts`.

## Update the list manually

```bash
git clone --depth 1 https://github.com/awesome-android-root/awesome-android-root.git
python3 tools/update_data.py awesome-android-root
```

This rewrites `app/src/main/assets/root_data.json`.

## Project layout

```
app/src/main/java/com/rootdiscover/app/
  MainActivity.kt   tabs, search & filters
  Adapters.kt       app list and devices list
  Data.kt           JSON loading and models
  Links.kt          open / copy links
app/src/main/assets/root_data.json   bundled catalogue
tools/update_data.py                 regenerates the catalogue
.github/workflows/build-apk.yml      builds the APK on GitHub
```

## Disclaimer

Rooting and unlocking a bootloader can wipe data, void warranty, trip Samsung Knox and break banking
apps. Root Discover only lists links; it does not root your device. Listed projects belong to their
authors and are not affiliated with this app.

## License

App code: MIT. Catalogue data: © Awesome Android Root contributors, MIT License.
