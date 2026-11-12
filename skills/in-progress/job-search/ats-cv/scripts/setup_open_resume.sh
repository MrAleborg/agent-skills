#!/usr/bin/env bash
# Builds a headless CLI around open-resume's PDF parser (the same code as
# https://www.open-resume.com/resume-parser) into $ATS_CV_CACHE/or-cli.js.
# open-resume is AGPL-3.0, so it is fetched at a pinned commit, never vendored.
# Idempotent: re-running is a no-op once the bundle exists.
set -euo pipefail

CACHE="${ATS_CV_CACHE:-$HOME/.cache/ats-cv}"
COMMIT=4f8255a2c763479837f69f1dccf2a3338730cd79
HERE="$(cd "$(dirname "$0")" && pwd)"

if [ -f "$CACHE/or-cli.js" ] && [ -d "$CACHE/deps/node_modules/pdfjs-dist" ]; then
  echo "$CACHE/or-cli.js"; exit 0
fi
mkdir -p "$CACHE"

if [ ! -d "$CACHE/open-resume/.git" ]; then
  git clone --quiet https://github.com/xitanggg/open-resume.git "$CACHE/open-resume"
fi
git -C "$CACHE/open-resume" checkout --quiet "$COMMIT"

# Only the three packages the parser needs, kept out of open-resume's own tree
# so its full Next.js dependency set is never installed.
mkdir -p "$CACHE/deps"
[ -f "$CACHE/deps/package.json" ] || echo '{"private":true}' > "$CACHE/deps/package.json"
npm install --prefix "$CACHE/deps" --ignore-scripts --no-audit --no-fund --silent \
  @reduxjs/toolkit@1.9.5 pdfjs-dist@3.7.107 esbuild@0.21.5

cp "$HERE/open_resume_cli.ts" "$CACHE/open-resume/src/app/cli-entry.ts"
# The entry sits under open-resume's baseUrl (src/app) so its `lib/...` imports resolve.
(cd "$CACHE/open-resume" && NODE_PATH="$CACHE/deps/node_modules" \
  "$CACHE/deps/node_modules/.bin/esbuild" src/app/cli-entry.ts --bundle --platform=node \
  --external:pdfjs-dist --outfile="$CACHE/or-cli.js" --log-level=error)

echo "$CACHE/or-cli.js"
