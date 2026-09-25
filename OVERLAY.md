# Xun2202 overlay of Keiyoushi extensions

This fork of [keiyoushi/extensions-source](https://github.com/keiyoushi/extensions-source) is an
**overlay**: it keeps the whole upstream tree so it can be synced regularly, but CI only builds and
publishes the handful of modules listed in [`.github/overlay-modules.txt`](.github/overlay-modules.txt).

The published repo lives in [Xun2202/extensions](https://github.com/Xun2202/extensions) and is added
to Mihon (0.20.1+) with:

```
https://github.com/Xun2202/extensions/raw/repo/index.pb
```

Use it *alongside* the official Keiyoushi repo. Only install the overlay modules from here; keep
everything else on Keiyoushi.

## What is in the overlay

| Module | Why it is here |
| --- | --- |
| `all/asmhentai` | Restores `totalPagesSelector = "t_pages"` (upstream regression from #19161 that limits galleries to 10 pages). Drop once upstream fixes it. |
| `all/ehentai`, `all/hitomi`, `all/nhentai`, `all/pururin`, `en/hentai20`, `en/hentai2read` | Removed from Keiyoushi after the 2026 DMCA notices; sources carried over from [yuzono/cursed-manga-extensions](https://github.com/yuzono/cursed-manga-extensions). |

## Local changes vs upstream

Everything overlay-specific is confined to:

- `.github/overlay-modules.txt` - the whitelist.
- `.github/scripts/github_utils.py` - reads the whitelist, `PUBLISH_REPO` / `SOURCE_REPO` env vars.
- `.github/scripts/generate-build-matrices.py` - filters the build/delete matrices by the whitelist.
- `.github/scripts/publish-repo.py` - filters the published index by the whitelist; repo identity
  (name, badge, signing-key fingerprint, contact) comes from env vars.
- `.github/scripts/cleanup-releases.py` - uses `SOURCE_REPO` from `github_utils`.
- `.github/workflows/build_push.yml`, `.github/workflows/cleanup_releases.yml` - repo targets and
  env vars; the `github.repository == 'keiyoushi/...'` gates are removed.
- `src/all/asmhentai` - the fix above (versionCode bumped).
- The six carried-over source directories.

## Routine maintenance

Upstream is merged automatically every 3 days by [`.github/workflows/sync_upstream.yml`](.github/workflows/sync_upstream.yml)
(merge, never rebase; this fork's `.github/workflows/**` are always kept as-is; any other conflict fails the
run and GitHub emails the owner). CI is triggered after a successful merge. To sync by hand:

```bash
git fetch upstream
git merge upstream/main
# resolve conflicts if any (normally only in the files listed above)
git push
```

CI rebuilds whichever whitelisted modules were touched. To add or retire a module, edit
`.github/overlay-modules.txt`; retired modules disappear from the published index on the next run.

## Required repository secrets

`SIGNING_KEY` (base64 of the JKS keystore), `ALIAS`, `KEY_STORE_PASSWORD`, `KEY_PASSWORD`, and
`BOT_PAT` (a token with `repo` scope on `Xun2202/extensions`, used to push the `repo` branch and
upload release assets).
