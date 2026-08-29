# XSHELF Homebrew tap

This tap installs the architecture-specific, Developer ID-signed and notarized
XSHELF archives published with the upstream release.

## Bottle pilot

Pull requests that change the XSHELF formula run Homebrew's bottle lifecycle on
native Apple silicon and native Intel GitHub runners. Each job builds with
`brew test-bot --only-formulae` (which uses Homebrew's bottle commands), checks
the generated bottle JSON, and proves that the source, bottled, poured, and
forced archive-fallback binaries have identical bytes and code-signature
evidence.

The two upstream archive URLs and checksums in `Formula/xshelf.rb` remain the
stable fallback whenever a matching bottle is unavailable or a user requests
`--build-from-source`.

Bottle publication is a separate manual gate. Before running `brew pr-pull`,
review both workflow artifacts and require exactly these native jobs:

- `bottle (macos-15)`: Apple silicon
- `bottle (macos-15-intel)`: Intel

The publish workflow requires the reviewed pull request head SHA and passes it
to `brew pr-pull --head-sha`. Do not run it if either bottle archive, bottle
JSON file, or `bottle-proof.<tag>.json` record is missing or inconsistent.
