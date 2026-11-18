#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$ROOT/.android-build"
mkdir -p "$TOOLS"
cd "$TOOLS"

if [ ! -x "$TOOLS/jdk/bin/java" ]; then
  echo "Downloading JDK 17"
  curl -fsSL -o jdk.tar.gz "https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jdk/hotspot/normal/eclipse?project=jdk"
  rm -rf jdk-tmp jdk
  mkdir -p jdk-tmp
  tar -xzf jdk.tar.gz -C jdk-tmp
  mv jdk-tmp/jdk-* jdk
fi
export JAVA_HOME="$TOOLS/jdk"
export PATH="$JAVA_HOME/bin:$PATH"
java -version

export ANDROID_HOME="$TOOLS/sdk"
if [ ! -x "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" ]; then
  echo "Downloading Android command line tools"
  curl -fsSL -o cmdtools.zip "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
  rm -rf "$ANDROID_HOME/cmdline-tools"
  mkdir -p "$ANDROID_HOME/cmdline-tools"
  unzip -q cmdtools.zip -d "$ANDROID_HOME/cmdline-tools"
  mv "$ANDROID_HOME/cmdline-tools/cmdline-tools" "$ANDROID_HOME/cmdline-tools/latest"
fi

yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --sdk_root="$ANDROID_HOME" --licenses >/dev/null || true
"$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --sdk_root="$ANDROID_HOME" "platforms;android-34" "build-tools;34.0.0"

if [ ! -x "$TOOLS/gradle-8.7/bin/gradle" ]; then
  echo "Downloading Gradle"
  curl -fsSL -o gradle.zip "https://services.gradle.org/distributions/gradle-8.7-bin.zip"
  unzip -q gradle.zip -d "$TOOLS"
fi
export PATH="$TOOLS/gradle-8.7/bin:$PATH"

printf 'sdk.dir=%s\n' "$ANDROID_HOME" > "$ROOT/android/local.properties"
cd "$ROOT/android"
gradle assembleDebug --no-daemon
cp -f app/build/outputs/apk/debug/app-debug.apk "$ROOT/PocketDoc.apk"
mkdir -p /home/zahid/Downloads
cp -f "$ROOT/PocketDoc.apk" /home/zahid/Downloads/PocketDoc.apk
ls -lh "$ROOT/PocketDoc.apk" /home/zahid/Downloads/PocketDoc.apk
echo "APK_READY"
