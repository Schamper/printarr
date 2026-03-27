# 🖨️ printarr

> *"prowlarr but for plastic" — me, to myself, at 2am*

my boy claude cooked this up. it's a self-hosted *arr-style app for hoarding 3D model files you'll never actually print. searches thingiverse, printables, makerworld, myminifactory, cults3d, and makeronline simultaneously, streams results live, lets you bookmark stuff into a library, tag it, queue it up with filament settings, fire them straight into your slicer. dopamine machine for 3D printer goblins.

looks like *arr. does not judge you for having 4000 saved models and a single ender 3.

> ⚠️ **keep this on your local network.** this thing was vibed into existence at 2am with zero threat modeling — no auth, no rate limiting, cors wide open like your mom's refrigerator. if you expose it to the internet you deserve what happens next.

---

## 🚀 just run it bro

```bash
docker compose up -d
```

go to [http://localhost:6969](http://localhost:6969) and start doom-scrolling printables at work.

---

## 🐳 docker compose (the real one)

```yaml
services:
  printarr:
    image: ghcr.io/schamper/printarr:latest
    container_name: printarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
    volumes:
      - /your/config:/config      # db lives here
    ports:
      - 6969:6969
    restart: unless-stopped
```

### volumes

| path | what lives there |
|------|-----------------|
| `/config` | sqlite db, settings, vibes |

### env vars

| var | default | description |
|-----|---------|-------------|
| `PUID` | `1000` | linux user id (chown stuff) |
| `PGID` | `1000` | linux group id (chown stuff) |
| `TZ` | `UTC` | timezone so timestamps aren't insane |
| `LOG_LEVEL` | `INFO` | set to DEBUG if you want chaos |

want a different port to yell at? change the left side of `ports:` in your compose file. `8080:6969` = host 8080 → container 6969.

---

## 🔑 api keys (actually required this time, sorry)

some sources are gatekeeping little gremlins. configure in **Settings → Indexers**.

**Thingiverse** — demands an App Token or it throws a 401 at you and walks away.\
no token = no thingiverse. that's the deal. go to https://www.thingiverse.com/apps/create, make an app, copy the **App Token** value, paste it in settings. takes like 2 minutes. worth it for the drm-free printer farm.

**MyMiniFactory** — also wants a key. https://www.myminifactory.com/settings/developer. generate one. it's free. paste it. done.

**the rest** (Printables, MakerWorld, Cults3D, MakerOnline) — no keys needed, they're normal websites that haven't read the enshittification playbook yet. (makerworld uses a chrome impersonation hack because cloudflare said no and we said lol ok)

---

## 🏷️ tags & grouping

click the little tag icon on any library card. type a tag, hit enter. that's it. you can:

- filter by tag (click any tag chip)
- group the whole library by tag (toggle in header)
- use the tag bar at the top for quick filtering

it's like collections but not cringe.

---

## 🖨 print queue

hit **Files** on any library card, then **Queue** next to any file. it gets added to the queue tab as a specific file — not just "the model", the actual file you want to print. because remembering which STL out of 47 in a model pack you wanted is not a skill you have.

the queue lets you set filament type, color, copies, and notes per item. all inline-editable. drag to reorder. **Slice ▾** fires it straight into your slicer. download button if you want the file locally. trash it when done. that's the whole workflow.

unlike the windows print spooler, items here can actually be removed. wild concept. no need to restart the spooler service, open task manager, kill `spoolsv.exe`, reboot, pray, reboot again, give up and walk to the printer to cancel it physically.

---

## 📥 downloads

click the **Files** button on any library card. then:

- **Download** → browser downloads the file directly.
- **Queue** → adds the file to your print queue.
- **Slice ▾** → fires a protocol handler to PrusaSlicer, OrcaSlicer, or Bambu Studio. slicer opens and imports the file automatically.

not running a slicer locally? just use Download and it'll land in your browser's downloads folder like a normal person.

---

## 🖥️ dev setup (for the ~brave~ llm, let's be honest)

### backend

```bash
uv sync
uv run uvicorn app.main:app --reload --port 6969
```

or with just:

```bash
just dev          # backend only, hot reload
just dev-frontend # vite frontend, proxies to :6969
just dev-rebuild  # rebuild frontend assets then restart backend
```

vite runs on :3000 and proxies `/api` to the backend. hot reload and everything. you're welcome.

### docker

```bash
just up           # docker compose up (uses existing image)
just up-detached  # same but in the background, like a coward
just docker-build # build the image
just down         # stop everything
```

### other useful stuff

```bash
just install   # install all deps (backend + frontend)
just build     # build frontend into static/ + sync python deps
just test      # run pytest
just format    # ruff fix + format
just db        # open sqlite shell on the live db
just db-queue  # peek at the print queue
```

---

## license

mit. do whatever. print something cool.
