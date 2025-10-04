"""
Performance optimization utilities for the image classifier service
"""

import time
import psutil
import threading
import queue
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import gc
import os

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    response_time: float
    throughput: float
    active_connections: int


class PerformanceMonitor:
    """Monitor system performance during load testing"""
    
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.metrics: List[PerformanceMetrics] = []
        self.monitoring = False
        self.monitor_thread = None
        self.response_times = queue.Queue()
        self.throughput_counter = 0
        self.start_time = None
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.start_time = time.time()
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Performance monitoring stopped")
    
    def record_response_time(self, response_time: float):
        """Record a response time measurement"""
        self.response_times.put(response_time)
    
    def record_throughput(self):
        """Record a throughput measurement"""
        self.throughput_counter += 1
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_mb = memory.used / 1024 / 1024
                
                # Calculate average response time
                response_times = []
                while not self.response_times.empty():
                    try:
                        response_times.append(self.response_times.get_nowait())
                    except queue.Empty:
                        break
                
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                
                # Calculate throughput
                current_time = time.time()
                elapsed_time = current_time - self.start_time if self.start_time else 1
                throughput = self.throughput_counter / elapsed_time
                
                # Count active connections (approximate)
                active_connections = len(psutil.net_connections())
                
                # Store metrics
                metric = PerformanceMetrics(
                    timestamp=current_time,
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    memory_mb=memory_mb,
                    response_time=avg_response_time,
                    throughput=throughput,
                    active_connections=active_connections
                )
                
                self.metrics.append(metric)
                
                # Log current metrics
                logger.debug(f"CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}% "
                           f"({memory_mb:.1f}MB), Response Time: {avg_response_time:.3f}s, "
                           f"Throughput: {throughput:.2f} req/s")
                
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.interval)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics"""
        if not self.metrics:
            return {}
        
        cpu_values = [m.cpu_percent for m in self.metrics]
        memory_values = [m.memory_percent for m in self.metrics]
        memory_mb_values = [m.memory_mb for m in self.metrics]
        response_times = [m.response_time for m in self.metrics if m.response_time > 0]
        throughput_values = [m.throughput for m in self.metrics]
        
        return {
            'duration': self.metrics[-1].timestamp - self.metrics[0].timestamp,
            'cpu_avg': sum(cpu_values) / len(cpu_values),
            'cpu_max': max(cpu_values),
            'memory_avg_percent': sum(memory_values) / len(memory_values),
            'memory_max_percent': max(memory_values),
            'memory_avg_mb': sum(memory_mb_values) / len(memory_mb_values),
            'memory_max_mb': max(memory_mb_values),
            'response_time_avg': sum(response_times) / len(response_times) if response_times else 0,
            'response_time_max': max(response_times) if response_times else 0,
            'throughput_avg': sum(throughput_values) / len(throughput_values),
            'throughput_max': max(throughput_values),
            'samples': len(self.metrics)
        }


class ConnectionPool:
    """Connection pool for HTTP requests"""
    
    def __init__(self, max_connections: int = 100, max_keepalive: int = 20):
        self.max_connections = max_connections
        self.max_keepalive = max_keepalive
        self.session_pool = queue.Queue(maxsize=max_connections)
        self.active_sessions = 0
        self.lock = threading.Lock()
    
    def get_session(self):
        """Get a session from the pool"""
        try:
            return self.session_pool.get_nowait()
        except queue.Empty:
            if self.active_sessions < self.max_connections:
                with self.lock:
                    if self.active_sessions < self.max_connections:
                        self.active_sessions += 1
                        import requests
                        session = requests.Session()
                        adapter = requests.adapters.HTTPAdapter(
                            pool_connections=1,
                            pool_maxsize=self.max_keepalive
                        )
                        session.mount('http://', adapter)
                        session.mount('https://', adapter)
                        return session
            return None
    
    def return_session(self, session):
        """Return a session to the pool"""
        try:
            self.session_pool.put_nowait(session)
        except queue.Full:
            with self.lock:
                self.active_sessions -= 1
            session.close()


class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    @staticmethod
    def optimize_python_gc():
        """Optimize Python garbage collection"""
        # Set GC thresholds for better performance
        gc.set_threshold(700, 10, 10)
        logger.info("Python GC thresholds optimized")
    
    @staticmethod
    def optimize_system_limits():
        """Optimize system limits for better performance"""
        try:
            import resource
            
            # Increase file descriptor limit
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))
            
            logger.info(f"File descriptor limit increased to {hard}")
        except Exception as e:
            logger.warning(f"Could not optimize system limits: {e}")
    
    @staticmethod
    def optimize_environment():
        """Optimize environment variables for better performance"""
        # Set optimal environment variables
        os.environ['PYTHONUNBUFFERED'] = '1'
        os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
        
        # Optimize for CPU-bound tasks
        os.environ['OMP_NUM_THREADS'] = str(psutil.cpu_count())
        os.environ['MKL_NUM_THREADS'] = str(psutil.cpu_count())
        
        logger.info("Environment variables optimized for performance")
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get system information for optimization"""
        return {
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/')._asdict(),
            'platform': os.name,
            'python_version': os.sys.version
        }


class LoadBalancer:
    """Simple load balancer for testing"""
    
    def __init__(self, endpoints: List[str]):
        self.endpoints = endpoints
        self.current_index = 0
        self.lock = threading.Lock()
    
    def get_next_endpoint(self) -> str:
        """Get next endpoint in round-robin fashion"""
        with self.lock:
            endpoint = self.endpoints[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.endpoints)
            return endpoint
    
    def get_random_endpoint(self) -> str:
        """Get random endpoint"""
        import random
        return random.choice(self.endpoints)


class CachingLayer:
    """Simple caching layer for performance optimization"""
    
    def __init__(self, max_size: int = 1000, ttl: float = 300):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    return value
                else:
                    del self.cache[key]
            return None
    
    def set(self, key: str, value: Any):
        """Set value in cache"""
        with self.lock:
            # Remove oldest entries if cache is full
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.cache.keys(), 
                               key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
            
            self.cache[key] = (value, time.time())
    
    def clear(self):
        """Clear cache"""
        with self.lock:
            self.cache.clear()
    
    def size(self) -> int:
        """Get cache size"""
        with self.lock:
            return len(self.cache)


def profile_function(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """Profile a function's performance"""
    import cProfile
    import pstats
    import io
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    
    profiler.disable()
    
    # Get profiling stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats()
    
    return {
        'result': result,
        'execution_time': end_time - start_time,
        'profile_stats': s.getvalue()
    }


def memory_usage(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """Measure memory usage of a function"""
    process = psutil.Process()
    
    # Get initial memory usage
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Run function
    result = func(*args, **kwargs)
    
    # Get final memory usage
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    return {
        'result': result,
        'initial_memory_mb': initial_memory,
        'final_memory_mb': final_memory,
        'memory_delta_mb': final_memory - initial_memory
    }
