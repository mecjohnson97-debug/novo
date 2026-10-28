
## Fix (2026-06, session 3)
- Render backend crash: top-level `emergentintegrations` import (not in requirements_render.txt) -> made lazy; translation falls back to Groq/OpenAI/OpenRouter. This was why photos/videos failed on Render.
- Job search: never errors; 13 regions (br, pt, fr, be, ch, es, it, de, gb, us, ca, latam, remote); JSearch (local, needs RAPIDAPI_KEY) + free Jobicy/Remotive/Arbeitnow; region-specific platforms (Catho, InfoJobs, Vagas, Gupy, Net-Empregos, StepStone, Reed...)
- Video upload accepts files without mime (by extension); video responses skip gzip; clearer photo/video error messages
## Backlog
- Set RAPIDAPI_KEY on Render for local (non-remote) jobs
- Delete own posts (also removes GridFS video)
