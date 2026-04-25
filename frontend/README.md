# Agent gateway UI

- **Bun** package manager (`bun install`)
- **Vite** + **React** + **TypeScript**
- **Tailwind CSS v4** via `@tailwindcss/vite` — styles live in Tailwind utility classes; a single entry [`src/app.css`](src/app.css) contains `@import "tailwindcss";`
- **Biome** for format + lint (`bun run lint`, `bun run lint:fix`)

```bash
bun install
bun run dev
bun run build
```

Set `VITE_GATEWAY_URL` (see `.env.example`) to your FastAPI gateway.
