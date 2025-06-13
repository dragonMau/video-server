@echo off
for /f "usebackq tokens=1,* delims==" %%A in ("./edge/.env.local") do (
  set %%A=%%B
)

deno run -E -N ./edge/src/main.ts
