#!/bin/sh
# Install Eyrie on macOS or Linux (docs/packaging.md §7.1).
#
#   curl -fsSL https://alenabraham.me/eyrie/install.sh | sh
#   curl -fsSL https://alenabraham.me/eyrie/install.sh | sh -s -- --server-only
#
# Downloads the release for this OS and CPU from GitHub, checks it against the release's
# SHA256SUMS, installs it, and starts Eyrie's background service. Options:
#   --version vX.Y.Z   a specific release (default: the latest)
#   --server-only      server and web UI only, no tray widget (servers, SSH boxes), under ~/.local;
#                      no root needed (macOS and Linux)
#   --user             same as --server-only
#   --uninstall        remove the service and Eyrie itself; ~/.eyrie (your data) is never touched
#   --dry-run          print what would happen, change nothing
#
# Reading before running is a good idea: curl -fsSL https://alenabraham.me/eyrie/install.sh | less
set -eu

REPO="${EYRIE_REPO:-abrahamalen/eyrie}"
# Tests point this at a local mirror of a release; normally GitHub's release downloads.
BASE="${EYRIE_DOWNLOAD_BASE:-}"
VERSION=""
SERVER_ONLY=0
UNINSTALL=0
DRY=0
PORT=8787
USER_LIB="$HOME/.local/lib/eyrie"
USER_BIN="$HOME/.local/bin"

say() { printf '%s\n' "$*"; }
die() { printf 'eyrie install: %s\n' "$*" >&2; exit 1; }
run() {
    say "\$ $*"
    [ "$DRY" = 1 ] || "$@"
}
need() { command -v "$1" >/dev/null 2>&1 || die "needs $1"; }

while [ $# -gt 0 ]; do
    case "$1" in
        --version) [ $# -ge 2 ] || die "--version needs a value"; VERSION="$2"; shift ;;
        --server-only) SERVER_ONLY=1 ;;
        --user) SERVER_ONLY=1 ;;
        --uninstall) UNINSTALL=1 ;;
        --dry-run) DRY=1 ;;
        -h|--help) sed -n '2,17p' "$0" 2>/dev/null || true; exit 0 ;;
        *) die "unknown option: $1" ;;
    esac
    shift
done

OS=$(uname -s)
case "$(uname -m)" in
    arm64|aarch64) ARCH=aarch64 ;;
    x86_64|amd64) ARCH=x86_64 ;;
    *) die "unsupported CPU: $(uname -m)" ;;
esac
case "$OS" in Darwin|Linux) ;; *) die "unsupported OS: $OS (Windows is planned)" ;; esac

SUDO=""
if [ "$(id -u)" != 0 ]; then SUDO="sudo"; fi

# ---------------------------------------------------------------- uninstall

find_server() {
    for p in "$HOME/Applications/Eyrie.app/Contents/Resources/eyrie-server/eyrie-server" \
             "/Applications/Eyrie.app/Contents/Resources/eyrie-server/eyrie-server" \
             "/usr/lib/Eyrie/eyrie-server/eyrie-server" \
             "$USER_LIB/current/eyrie-server/eyrie-server"; do
        [ -x "$p" ] && { echo "$p"; return 0; }
    done
    return 1
}

if [ "$UNINSTALL" = 1 ]; then
    if exe=$(find_server); then
        run "$exe" service uninstall || say "(no background service to remove)"
    else
        say "No Eyrie server found; nothing to stop."
    fi
    if [ "$OS" = Darwin ]; then
        for app in "$HOME/Applications/Eyrie.app" "/Applications/Eyrie.app"; do
            [ -d "$app" ] && run rm -rf "$app"
        done
    else
        if command -v dpkg >/dev/null 2>&1 && dpkg -s eyrie >/dev/null 2>&1; then run $SUDO apt-get remove -y eyrie; fi
        if command -v rpm >/dev/null 2>&1 && rpm -q eyrie >/dev/null 2>&1; then run $SUDO dnf remove -y eyrie; fi
    fi
    [ -d "$USER_LIB" ] && run rm -rf "$USER_LIB"
    [ -L "$USER_BIN/eyrie-server" ] && run rm -f "$USER_BIN/eyrie-server"
    say "Eyrie is removed. Your data in ~/.eyrie and any running sessions were left alone."
    exit 0
fi

# ---------------------------------------------------------------- download and verify

need curl
need tar
if [ -z "$VERSION" ]; then
    # The latest full release (pre-releases are skipped, like the widget's update check).
    VERSION=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
        | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -1)
    [ -n "$VERSION" ] || die "couldn't find the latest release of $REPO"
fi
V=${VERSION#v}
[ -n "$BASE" ] || BASE="https://github.com/$REPO/releases/download/v$V"

if [ "$SERVER_ONLY" = 1 ]; then
    [ "$OS" = Darwin ] && PLATFORM=macos || PLATFORM=linux
    ASSET="eyrie-server-${V}-${PLATFORM}-${ARCH}.tar.gz"
    KIND=tar
elif [ "$OS" = Darwin ]; then
    [ "$ARCH" = aarch64 ] && A=aarch64 || A=x64
    ASSET="Eyrie_${V}_${A}.dmg"
    KIND=dmg
elif command -v apt-get >/dev/null 2>&1; then
    [ "$ARCH" = aarch64 ] && A=arm64 || A=amd64
    ASSET="Eyrie_${V}_${A}.deb"
    KIND=deb
elif command -v dnf >/dev/null 2>&1; then
    ASSET="Eyrie-${V}-1.${ARCH}.rpm"
    KIND=rpm
else
    say "No apt or dnf here: installing the server only, under ~/.local."
    ASSET="eyrie-server-${V}-linux-${ARCH}.tar.gz"
    KIND=tar
    SERVER_ONLY=1
fi

TMP=$(mktemp -d "${TMPDIR:-/tmp}/eyrie-install.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

say "Eyrie $V for $OS $ARCH: $ASSET"
curl -fsSL "$BASE/SHA256SUMS" -o "$TMP/SHA256SUMS" || die "couldn't download $BASE/SHA256SUMS"
WANT=$(awk -v f="$ASSET" '$2 == f || $2 == "*" f {print $1}' "$TMP/SHA256SUMS")
[ -n "$WANT" ] || die "$ASSET isn't in this release's SHA256SUMS"
curl -fSL --progress-bar "$BASE/$ASSET" -o "$TMP/$ASSET" || die "couldn't download $ASSET"
if command -v sha256sum >/dev/null 2>&1; then
    GOT=$(sha256sum "$TMP/$ASSET" | awk '{print $1}')
else
    GOT=$(shasum -a 256 "$TMP/$ASSET" | awk '{print $1}')
fi
[ "$GOT" = "$WANT" ] || die "checksum mismatch for $ASSET (expected $WANT, got $GOT); not installing"
say "Checksum OK."

# ---------------------------------------------------------------- install

case "$KIND" in
    dmg)
        APPS="$HOME/Applications"
        run mkdir -p "$APPS"
        MNT="$TMP/mnt"
        run hdiutil attach "$TMP/$ASSET" -mountpoint "$MNT" -nobrowse -quiet
        [ -d "$APPS/Eyrie.app" ] && run rm -rf "$APPS/Eyrie.app"
        run cp -R "$MNT/Eyrie.app" "$APPS/"
        run hdiutil detach "$MNT" -quiet
        # curl doesn't set the quarantine flag, so this unsigned build opens without the
        # "can't be opened" dialog a browser download gets.
        RES="$APPS/Eyrie.app/Contents/Resources"
        EXE="$RES/eyrie-server/eyrie-server"
        UI="$RES/ui"
        ;;
    deb)
        run $SUDO apt-get install -y "$TMP/$ASSET"
        EXE=/usr/lib/Eyrie/eyrie-server/eyrie-server
        UI=/usr/lib/Eyrie/ui
        ;;
    rpm)
        run $SUDO dnf install -y "$TMP/$ASSET"
        EXE=/usr/lib/Eyrie/eyrie-server/eyrie-server
        UI=/usr/lib/Eyrie/ui
        ;;
    tar)
        DEST="$USER_LIB/$V"
        run mkdir -p "$USER_LIB" "$USER_BIN"
        [ -d "$DEST" ] && run rm -rf "$DEST"
        run mkdir -p "$DEST"
        run tar -xzf "$TMP/$ASSET" -C "$DEST" --strip-components=1
        run ln -sfn "$DEST" "$USER_LIB/current"
        run ln -sfn "$USER_LIB/current/eyrie-server/eyrie-server" "$USER_BIN/eyrie-server"
        EXE="$USER_LIB/current/eyrie-server/eyrie-server"
        UI="$USER_LIB/current/ui"
        ;;
esac

# ---------------------------------------------------------------- service

if run "$EXE" service install --port "$PORT" --ui-dir "$UI"; then
    say ""
    say "Eyrie is running: http://127.0.0.1:$PORT"
else
    # No launchd/systemd user session (containers, some minimal servers): run it by hand.
    say ""
    say "Installed, but the background service couldn't be set up here."
    say "Start Eyrie yourself with:  EYRIE_SERVER__UI_DIR=\"$UI\" \"$EXE\" serve --port $PORT"
fi
if [ "$KIND" = dmg ] && [ "$SERVER_ONLY" = 0 ]; then
    run open "$APPS/Eyrie.app"
    say "The Eyrie widget is in your menu bar."
elif [ "$SERVER_ONLY" = 0 ]; then
    say "Start the tray widget from your app launcher (Eyrie), or run: eyrie-widget"
fi
if [ "$KIND" = tar ]; then
    case ":$PATH:" in *":$USER_BIN:"*) ;; *) say "Add $USER_BIN to your PATH to run eyrie-server directly." ;; esac
fi
say "Open http://127.0.0.1:$PORT to finish setup. Uninstall: curl -fsSL https://alenabraham.me/eyrie/install.sh | sh -s -- --uninstall"
[ "$DRY" = 1 ] && say "(dry run: the commands above were printed, nothing was changed)"
exit 0
