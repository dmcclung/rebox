# rebox

A passwordless authentication system for mail servers.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file based on the `.env.template` file. Fill in the values for the following variables:

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rebox_mail
export SECRET_KEY=change-me
export RP_ID=mail.rebox.sh
export RP_NAME=Rebox Mail
```
Try `openssl rand -hex 32` to generate a random secret key.


## Usage

```bash
python app.py
```
