# Brand assets (canonical for HACS)

SVG sources are synced from [ESP32-router/assets/brand](https://github.com/Balansun/ESP32-router/tree/main/assets/brand) — edit there only (`balansun-icon-light.svg`, `balansun-icon-dark.svg`, logos).

Regenerate PNGs for Home Assistant 2026.3+:

```bash
export BALANSUN_ROUTER_ROOT=/path/../Balansun-Router   # optional if sibling repo; BALANSUN_ESP32_ROOT is deprecated
npm run prepare:brand
```

This updates `custom_components/balansun/brand/*.png` per [inline brand images](https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api/) (256/512 icon, logo shortest side 128–512).
