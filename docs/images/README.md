# Images and promotional assets

All current screenshots were captured on 2026-09-18 from the running Atelier application at a desktop viewport of 1260 x 900. They replace the historical catalogue captures previously used in the README.

## Provenance

- The demo is launched with `scripts/run_demo.py`. It has a separate database and a visible **Demo collection** label.
- Its 16 original procedural colour studies are produced by `scripts/demo_art.py` using Pillow. They do not reproduce an existing artist's work. The generator and its original output use the repository's MIT license.
- Catalogue titles, dates, prices, venues, contacts, correspondence, and research details are synthetic. Contact addresses use reserved example domains. No real mailbox, provider response, or private installation is pictured.
- Screenshots show the real HTML interface and records from the local demo. No fabricated UI panels, connected-service states, or external-search results were composited into them.
- The promotional graphic combines two of those screenshots with typography and decorative window frames. `promo.html` is its editable source. Its labels identify the screens as a synthetic demo.
- Published raster files are re-encoded without EXIF or location metadata. Capture-only files and the demo database are ignored.

## Downloads

| Asset | Size | Use |
| --- | --- | --- |
| [Promotional graphic, PNG](atelier-promo.png) | 2400 x 1260 | LinkedIn posts, project presentations, sharing |
| [Promotional graphic, JPEG](atelier-promo.jpg) | 2400 x 1260 | README and smaller downloads |
| [GitHub social preview](atelier-social-preview.png) | 1280 x 640 | Repository Settings, General, Social preview |
| [Editable composition](promo.html) | 2400 x 1260 canvas | Open alongside this folder's images; export with a browser screenshot |

The composition uses Playfair Display and DM Sans through Google Fonts, with local serif/sans-serif fallbacks. Its screenshots retain the app's own typography. All nine screenshots are linked from the [walkthrough](../WALKTHROUGH.md).

When making new captures, use the isolated demo, allow images to finish loading, and review every visible record. Re-encode final images without metadata. Do not substitute screenshots of a private catalogue or mailbox.
