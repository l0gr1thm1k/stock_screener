import os

from prometheus_client import multiprocess


def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)



HOST_PORT = int(os.getenv('HOST_PORT', 8000))
N_WORKERS = int(os.getenv('GUNICORN_WORKERS', 2))
N_THREADS = int(os.getenv('GUNICORN_THREADS', 1))

bind = f'0.0.0.0:{HOST_PORT}'
loglevel = 'info'
workers = N_WORKERS
worker_class = 'gthread'
threads = N_THREADS
timeout = 60
graceful_timeout = 30
# Default ELB idle timeout is 60
keepalive = 75
preload_app = True
reload = True
        
