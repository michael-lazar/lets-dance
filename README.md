# Let's Dance 💃

*Let's Dance* is a humble [Spring '83](https://github.com/robinsloan/spring-83-spec) server written in django.

Now live at [https://spring83.mozz.us](https://spring83.mozz.us)

## Requirements

- python 3.10
- a strong constitution

## Development

```bash
# Download the source
git clone https://github.com/michael-lazar/lets-dance
cd django83/

# Initialize a virtual environment and install pip dependencies, etc.
tools/boostrap

# Create a user account for the admin dashboard
tools/manage createsuperuser

# Launch a local server
tools/start 127.0.0.1:8000

# Initialize pre-commit hooks
pre-commit install

# Run the tests, linters, etc.
tools/pytest
tools/mypy

# Tinker with the database
sqlite3 data/lets-dance.sqlite3

# Rebuild requirements
tools/pip-compile
tools/pip-install

# Generate a usable ed25519 key
tools/manage generate_keypair

# Seed your database with fake boards
tools/manage seed_boards --count 100

# Publish a board to any server
echo "<h1>Hello World!</h1>" | tools/manage publish_board \
    --content-file - \
    --public-key <public key> \
    --private-key <private key> \
    --server-url http://127.0.0.1:8000

# Check your local weather forecast
curl http://wttr.in
```

## Deploying to Production

You're on your own!
