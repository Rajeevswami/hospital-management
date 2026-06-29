"""Gunicorn production config. Run with: gunicorn -c deploy/gunicorn_config.py hospital_system.wsgi"""
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1   # standard formula for worker count
worker_class = "sync"
timeout = 60
accesslog = "/var/log/hospital_system/access.log"
errorlog = "/var/log/hospital_system/error.log"
loglevel = "info"
