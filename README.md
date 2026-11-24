# Imvula OS
**Understand the risk. Prioritise the fix.**

Imvula OS is a unified business platform developed by Imvula Labs. It helps small businesses protect their digital assets, automate repetitive tasks, and coordinate AI agents through one connected experience.

## The Three Suites
1. **Quantum Shield AI (PROTECT):** Cybersecurity risk management, asset visibility, and remediation tracking.
2. **Imvula AI Automation Suite (OPERATE):** Task management and workflow automation.
3. **Imvula Guardian AI (COORDINATE):** Governance, approval gates, and tracking for AI agents.

## Technology Stack
- **Frontend:** Vanilla HTML/CSS/JS (Hosted on GitHub Pages)
- **Backend:** Python 3.12, FastAPI, SQLAlchemy
- **Database:** PostgreSQL (Production), SQLite (Local/Test)
- **Migrations:** Alembic
- **Auth:** JWT + Bcrypt
- **Deployment:** Render (Backend API + DB)

## Live Environment
- **Public Website:** [https://zithaewarty-11.github.io/imvulalabs.github.io/](https://zithaewarty-11.github.io/imvulalabs.github.io/)
- **API Health Check:** [https://imvula-os-api-xs76.onrender.com/health](https://imvula-os-api-xs76.onrender.com/health)
- **API Documentation:** [https://imvula-os-api-xs76.onrender.com/docs](https://imvula-os-api-xs76.onrender.com/docs)

## Local Development
See `imvula-os/backend/DEPLOY.md` for detailed instructions on running the backend and frontend locally.

### Quick Start (Backend)
```bash
cd imvula-os/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your secret
alembic upgrade head
uvicorn app.main:app --reload
EQF
