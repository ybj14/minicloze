#!/usr/bin/env bash
# Post-sync patches so the PWA service worker works under Capacitor
# (https://localhost) and precaches data JSON for stronger offline.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WWW="$ROOT/www"
SW="$WWW/service-worker.js"
APPJS="$WWW/app.js"

test -f "$SW"
test -f "$APPJS"

mapfile -t DATA_FILES < <(find "$WWW/data" -type f -name '*.json' | sort | sed "s|^$WWW||")

perl - "$SW" "${DATA_FILES[@]}" <<'PERL'
use strict;
use warnings;
my $sw = shift @ARGV;
open my $fh, "<", $sw or die $!;
local $/; my $src = <$fh>; close $fh;

my @data = @ARGV;
my $data_js = join ",\n", map { "  \"$_\"" } @data;

$src =~ s/const CACHE_NAME = "[^"]+";/const CACHE_NAME = "minicloze-capacitor-v1";/;
if ($src =~ /const APP_SHELL = \[(.*?)\];/s) {
  my $shell = $1;
  $shell =~ s/\n\s*"\/data\/[^"]+",?//g;
  $shell =~ s/,\s*$//;
  $src =~ s/const APP_SHELL = \[.*?\];/const APP_SHELL = [$shell,\n$data_js\n];/s;
}

open my $out, ">", $sw or die $!;
print $out $src;
close $out;
PERL

perl -i -0pe 's#navigator\.serviceWorker\.register\([^;]+;#navigator.serviceWorker.register("/service-worker.js", { scope: "/" }).catch(() => {});#' "$APPJS"

if ! grep -q 'capacitor-offline' "$WWW/index.html"; then
  perl -i -pe 's#</title>#</title>\n    <meta name="minicloze-shell" content="capacitor-offline" />#' "$WWW/index.html"
fi

echo "Patched Capacitor offline assets in www/ (${#DATA_FILES[@]} data files precached)"
