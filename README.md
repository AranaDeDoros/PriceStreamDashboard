# PriceStream Dashboard API

This is the backend API for the PriceStream Dashboard. It provides endpoints for user authentication,
data retrieval from the **[PriceStream](https://github.com/AranaDeDoros/PriceStream)** service exposed endpoints, and serves as the core of the dashboard's functionality.

## Features

- User authentication with JWT tokens
- Integration with the PriceStream external API
- CORS support for frontend integration
- Asynchronous operations for improved performance

## Stack

- Python 3.10+
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- HTTPX

## TODO

- [ ] Add rotation of JWT secret keys for enhanced security
