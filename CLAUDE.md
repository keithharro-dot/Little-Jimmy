# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

No build step required. Open `index.html` directly in a browser. All dependencies are loaded via CDN or inline.

## Architecture

The entire application is a single file (`index.html`, ~4,500 lines) structured in three zones:

- **CSS** (lines ~13–303): Custom properties for theming (dark theme, asset-specific colors via `--gold`, `--btc`, etc.), layout grid, responsive breakpoints.
- **HTML** (lines ~305–4240): Markup for topbar, 3-column desktop layout, modals, auto sidebar, mobile tabs.
- **JavaScript** (lines ~4241–end): All app logic inline.

## Key State Objects

| Object | Purpose |
|--------|---------|
| `S` | Core trading state: positions, pending orders, account balance, settings |
| `TX` | Tax tracking: closed trade history, CGT calculations (37% AUD estimate) |
| `TV` | TradingView chart state: current asset, timeframe, scale calibration |
| `AE` | Auto engine config: confluence threshold, per-asset settings, scan interval |
| `MACRO` | Macro correlation: VIX, yields, DXY, regime detection |

State is persisted to `localStorage` (credentials, positions, balance, engine settings).

## Trading Instruments

9 assets: GOLD, SILVER, OIL (CFD only, up to 500:1 leverage) and BTC, ETH, SOL, XRP, DOGE (SPOT/CFD, up to 20:1) and NASDAQ (CFD, up to 100:1). Each has asset-specific leverage caps and defaults defined in the `markets` object.

## Data Flow

1. `fetchRealPrices()` — pulls live prices from CoinGecko (crypto) and Metals.live (gold); applies a ±0.12% random drift for demo mode.
2. Fast tick (3s) updates tickers; slow tick (8s) recalculates P&L, checks SL/TP triggers, and re-renders the trade overlay.
3. `renderTradeOverlay()` — draws entry/SL/TP lines on a `<canvas>` layered over the TradingView iframe. Requires manual chart scale calibration inputs to map price→pixel coordinates.
4. Auto engine (`toggleEngine()`) scans confluence conditions on a configurable interval, checks the macro regime and news blackout, then calls `executeTrade()` if signals align.
5. `computeMacroRegime()` classifies the market as STRONG RISK-ON → CRISIS based on live macro indicators and gates auto-trade entries per asset-specific rules.

## Capital.com Integration

`connectAPI()` handles OAuth/API credentials for live or demo accounts. Credentials are stored in `localStorage` (client-only). Read-only mode lets the user monitor a real account without placing trades.

## News Blackout

An economic calendar feed generates a ticker; HIGH-impact events block auto-trades for a configurable window (15/30/60 min). Manual override available.

## Mobile Layout

Detected via `max-width: 768px`. Switches to a tab-based navigation (Chart, Trade, Orders, Account, Auto) with swipe gesture support. `mobileTab()` manages tab switching.
