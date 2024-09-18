"""
Defines a memcache client that can be used to store and retrieve data from the memcache server.
"""
import os

from pymemcache.client import base

memcache_client = base.Client((
    os.getenv('MEMCACHED_HOST', 'memcached-service'),
    int(os.getenv('MEMCACHED_PORT', 11211))
))
