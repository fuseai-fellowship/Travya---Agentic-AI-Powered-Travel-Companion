## `initial-setup.md`

````markdown
# Travya — Initial Setup

This document explains the **initial setup** for Travya — Agentic AI Powered Travel Companion.  
It covers what we did so far, how to run it locally, and how to access all services.

---

## 1️⃣ What We Did So Far

- Set up **backend** using FastAPI.
- Set up **frontend** using Node.js + Vite, served via Nginx.
- Set up **PostgreSQL database** with persistent Docker volume.
- Added **Adminer** for DB management.
- Added **MailCatcher** for email testing.
- Added **Playwright container** for browser automation/testing.
- Added **Traefik proxy** to handle routing between services.
- Configured **Docker Compose** to orchestrate all containers.
- Added optional **Makefile** for simple commands.
- Verified that containers start correctly using `docker compose ps`.

---

## 2️⃣ Prerequisites

Make sure you have installed:

- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/)
- [Make](https://www.gnu.org/software/make/) (optional)

---

## 3️⃣ Clone the Repository

```bash
git clone https://github.com/fuseai-fellowship/Travya---Agentic-AI-Powered-Travel-Companion.git
cd Travya---Agentic-AI-Powered-Travel-Companion
````

---

## 4️⃣ Build and Start Services

Build all Docker images and start containers:

```bash
docker compose up -d --build
```

* `-d` runs containers in detached mode.
* `--build` forces rebuilding the images.

After the first build, you can start the containers faster:

```bash
docker compose up -d
```

---

## 5️⃣ Access the Services

Once the services are running, you can access them using the following URLs:

| Service      | URL                                                      |
| ------------ | -------------------------------------------------------- |
| Frontend     | [http://localhost:5173](http://localhost:5173)           |
| Backend API  | [http://localhost:8000/docs](http://localhost:8000/docs) |
| Adminer (DB) | [http://localhost:8080](http://localhost:8080)           |
| MailCatcher  | [http://localhost:1080](http://localhost:1080)           |

**Notes:**

* Backend API docs are available at `/docs`.
* `travya-prestart` container may exit after running initialization; this is normal.

---

## 6️⃣ Stop Services

To stop and remove all containers:

```bash
docker compose down
```

---

## 7️⃣ Optional Makefile

We can simplify commands using a `Makefile`:

```makefile
# Build and start services
up:
	docker compose up -d --build

# Start services without rebuilding
start:
	docker compose up -d

# Stop services
down:
	docker compose down

# View logs
logs:
	docker compose logs -f

# Access backend shell
backend-shell:
	docker compose exec backend bash
```

Usage examples:

```bash
make up            # Build & start all containers
make start         # Start without rebuilding
make logs          # Tail all logs
make backend-shell # Open backend container shell
make down          # Stop all containers
```

---

## 8️⃣ Notes / Troubleshooting

* Ensure ports **5173, 8000, 8080, 1080** are free.
* If containers fail to start, check logs:

```bash
docker compose logs <service-name>
```

* Rebuild a single service if needed:

```bash
docker compose build <service-name>
docker compose up -d <service-name>
```

* If frontend is not accessible at 5173, check that Nginx is mapping port 80 correctly.

```
