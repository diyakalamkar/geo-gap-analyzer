<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://ai.google.dev/static/site-assets/images/share-ais-513315318.png" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/f5b279c6-4366-4baf-bfb5-e69cb09d37b5

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

# GEO Gap Analyzer — frontend setup patch

This patch supplies the missing root `package.json` that causes `npm run dev` to fail with ENOENT.

## Apply
1. Copy `package.json` into `D:\seo-gap\geo-gap-analyzer\` (the same folder as `index.html` and `vite.config.ts`).
2. In PowerShell, from that folder run:

   ```powershell
   npm install
   npm run dev
   ```

3. If Vite reports that it cannot resolve `/src/main.tsx`, check that `src/main.tsx` exists and that `index.html` points to `/src/main.tsx`.

The uploaded component files import `../types`, so `src/types.ts` must also exist. This patch does not overwrite the existing components or Python pipeline.

## Integration direction (avoid duplicate dashboards)
Use React/Vite as the single user-facing dashboard. Keep Python for data processing and expose the validated exports to the React app via a small local API or generated JSON files. Do not embed a second Streamlit dashboard inside the React dashboard. Keep the existing React components for their distinct views; consolidate overlapping KPI cards and brand tables into one Overview/Explorer, and use the existing ProviderComparison, GeoGapExplorer, GeoGapSimulator, ProbingLab, LeaderboardsView, and TrendsView only where their data is genuinely available.
