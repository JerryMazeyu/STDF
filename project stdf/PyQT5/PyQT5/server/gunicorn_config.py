import multiprocessing

# 绑定的IP和端口
bind = "0.0.0.0:5000"

# 工作进程数
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = "sync"

# 每个工作进程的线程数
threads = 4

# 最大并发请求数
worker_connections = 1000

# 超时时间
timeout = 30

# 重启时间
graceful_timeout = 30

# 日志级别
loglevel = "info"

# 访问日志格式
accesslog = "gunicorn_access.log"
errorlog = "gunicorn_error.log"

# 进程名称
proc_name = "stdf_server"

# 预加载应用
preload_app = True

# 守护进程运行
daemon = False

# 调试模式
debug = False

# 重载
reload = False 