# Third-Party Notices

This package includes Netcad NCZ/NCA decoding code extracted from the 02CadGis
QGIS plugin.

## Jeomatik NCZ Reader (historical lineage)

**This section records history. It does not describe the code in this
package.**

The 02CadGis QGIS plugin shipped, in versions 0.1.0 through 4.1.2, an NCZ
decoder adapted from **Jeomatik NCZ Reader**:

- Copyright (C) 2026 Erdinç Örsan ÜNAL
- Upstream source: <https://github.com/erdincunal/Jeomatik-NCZ-Reader>
- Project page: <https://jeomatik.com/ncz-reader.html>
- Upstream license: GNU General Public License v2.0 or later (`GPL-2.0-or-later`)

The `ncz_engine` in this package is **not** that code. It has been the plugin's
v2 engine since this package's first release (0.1.0, 2026-08-25), and no
version of `cad2geo` has ever bundled the adapted v1 parser. The lineage is
recorded here because the engine was written for the 02CadGis plugin, whose
earlier releases carried that code, and because this package is kept in step
with that plugin.

The decoder in this package, and the SDK packaging around it, are:

- Copyright (C) 2026 Yusuf Eminoğlu

The v2 engine was written with knowledge of the upstream implementation, not
in isolation from it. It is offered as an independent implementation of the
format; it is not a legal opinion on the derivative-work status of any
particular version.

The Jeomatik name, logo, and associated trademarks are not used under the GPL
and remain the property of their respective owner. cad2geo is an independent
project and is not endorsed by or affiliated with Jeomatik.
