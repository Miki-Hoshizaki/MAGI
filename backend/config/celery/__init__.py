from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# 设置 Django 默认设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('magisys')

# 使用字符串，这样 worker 不用序列化配置对象
app.config_from_object('config.celery.celeryconfig')

# 从所有已注册的 app 中加载任务模块
app.autodiscover_tasks()