# Gunicorn configuration file for Nova Kanban Board
# /srv/nova_project_management/nova_project_management/gunicorn.conf.py

import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
errorlog = "/var/log/gunicorn/nova_kanban_error.log"
accesslog = "/var/log/gunicorn/nova_kanban_access.log"
loglevel = "info"

# Process naming
proc_name = "gunicorn_nova_kanban"

# Server mechanics
daemon = False
pidfile = "/var/run/gunicorn/nova_kanban.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Environment
raw_env = [
    'DJANGO_SETTINGS_MODULE=nova_workers_management.settings',
]

# Preload application for better performance
preload_app = True

# Worker process lifecycle
def on_starting(server):
    server.log.info("Starting Gunicorn server for Nova Kanban Board")

def on_reload(server):
    server.log.info("Reloading Gunicorn server")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def on_exit(server):
    server.log.info("Shutting down Gunicorn server")

# Performance tuning
forwarded_allow_ips = "127.0.0.1"
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}
