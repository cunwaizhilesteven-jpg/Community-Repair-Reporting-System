# Community Repair Reporting System

A system for community members to report and track repair requests in their neighborhood.

## Quick Start

1. **Read CLAUDE.md first** - Contains essential rules for Claude Code
2. Follow the pre-task compliance checklist before starting any work
3. Use proper module structure under `src/main/python/`
4. Commit after every completed task

## Project Structure

```
Community Repair Reporting System/
├── CLAUDE.md              # Essential rules for Claude Code
├── README.md              # This file
├── .gitignore             # Git ignore patterns
├── src/
│   ├── main/
│   │   ├── python/        # Python source code
│   │   │   ├── core/      # Core business logic
│   │   │   ├── utils/     # Utility functions
│   │   │   ├── models/    # Data models
│   │   │   ├── services/  # Service layer
│   │   │   └── api/       # API endpoints
│   │   └── resources/
│   │       ├── config/    # Configuration files
│   │       └── assets/    # Static assets
│   └── test/
│       ├── unit/          # Unit tests
│       └── integration/   # Integration tests
├── docs/                  # Documentation
├── tools/                 # Development tools
├── examples/              # Usage examples
└── output/                # Generated output files
```

## Development Guidelines

- **Always search first** before creating new files
- **Extend existing** functionality rather than duplicating
- **Use Task agents** for operations >30 seconds
- **Single source of truth** for all functionality
- **Commit after each feature**

## Getting Started

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies (when available)
pip install -r requirements.txt
```

## Teacher Test Delivery Checklist (Recommended)

For graduation-project demo/testing, provide the following package:

- `src/` (backend source)
- `miniprogram/` (WeChat Mini Program source)
- `requirements.txt`
- `.env.example`
- `src/main/resources/config/database.sql` (schema)
- `src/main/resources/config/test_data.sql` (test data)
- this `README.md`

## Backend Quick Run (Teacher Machine)

1. Create virtual environment and install dependencies:

```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

2. Configure environment variables:

- Copy `.env.example` to `.env`
- Update at least:
  - `DATABASE_URL`
  - `SECRET_KEY`
  - `JWT_SECRET_KEY`
- `WECHAT_APP_ID` and `WECHAT_APP_SECRET` can stay empty for local debug login.

3. Initialize database:

- Run `src/main/resources/config/database.sql`
- Then run `src/main/resources/config/test_data.sql`

4. Start backend:

```bash
python src/main/python/run.py
```

Default backend address: `http://127.0.0.1:5000`

## Teacher Testing Guide (No WeChat dependency)

This project already provides development login API (debug mode only):

- `POST /api/v1/auth/dev-login`
- Body example:

```json
{
  "openid": "admin_test_openid"
}
```

You can use these openid values from test data:

- super admin: `super_test_openid`
- admin: `admin_test_openid`
- repairman: `repair1_test_openid`
- resident: `resident1_test_openid`

The API returns JWT token for subsequent authorized requests.

## About test database and API key

- Yes, for teacher testing you should provide a **test database** setup, and you already did correctly with `database.sql` + `test_data.sql`.
- If your defense requires API keys, only provide a **test key** with limited permissions/rate limits.
- Never provide production keys/passwords in submission package.

## Suggested defense test flow

1. Start backend and import test data
2. Use `dev-login` to get tokens for each role
3. Verify role flows:
   - resident creates and tracks work orders
   - admin audits and assigns work orders
   - repairman processes and completes work orders
   - resident evaluates completed work orders
   - super admin manages users/buildings

## License

[Add your license here]
