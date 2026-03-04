"""
性能监控模块

提供响应时间监控、P95 计算和性能告警功能
"""
import logging
import time
from collections import deque
from typing import Dict, List, Optional, Deque
from dataclasses import dataclass, field
from threading import Lock
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    
    # 响应时间列表（最近 N 次调用）
    response_times: Deque[float] = field(default_factory=lambda: deque(maxlen=1000))
    
    # 总调用次数
    total_calls: int = 0
    
    # 成功调用次数
    successful_calls: int = 0
    
    # 失败调用次数
    failed_calls: int = 0
    
    # 总响应时间（用于计算平均值）
    total_response_time: float = 0.0
    
    # 线程锁
    lock: Lock = field(default_factory=Lock)


class PerformanceMonitor:
    """
    性能监控器
    
    功能：
    - 记录每次 API 调用的响应时间
    - 计算 P95 响应时间
    - 在响应时间超过阈值时记录警告
    - 提供性能统计报告
    """
    
    # 性能阈值（秒）
    P95_WARNING_THRESHOLD = 5.0  # P95 响应时间警告阈值
    SINGLE_CALL_WARNING_THRESHOLD = 10.0  # 单次调用警告阈值
    
    def __init__(self):
        """初始化性能监控器"""
        # 按模型分类的性能指标
        self._metrics_by_model: Dict[str, PerformanceMetrics] = {}
        
        # 全局性能指标
        self._global_metrics = PerformanceMetrics()
        
        logger.info("性能监控器已初始化")
    
    def record_call(
        self,
        model: str,
        response_time: float,
        success: bool = True,
        user_email: Optional[str] = None
    ) -> None:
        """
        记录 API 调用的响应时间
        
        Args:
            model: 模型名称（如 "deepseek/deepseek-chat"）
            response_time: 响应时间（秒）
            success: 调用是否成功
            user_email: 可选的用户邮箱
        """
        # 获取或创建模型的性能指标
        if model not in self._metrics_by_model:
            self._metrics_by_model[model] = PerformanceMetrics()
        
        metrics = self._metrics_by_model[model]
        
        # 更新指标（线程安全）
        with metrics.lock:
            metrics.response_times.append(response_time)
            metrics.total_calls += 1
            
            if success:
                metrics.successful_calls += 1
                metrics.total_response_time += response_time
            else:
                metrics.failed_calls += 1
        
        # 更新全局指标
        with self._global_metrics.lock:
            self._global_metrics.response_times.append(response_time)
            self._global_metrics.total_calls += 1
            
            if success:
                self._global_metrics.successful_calls += 1
                self._global_metrics.total_response_time += response_time
            else:
                self._global_metrics.failed_calls += 1
        
        # 检查单次调用是否超过阈值
        if response_time > self.SINGLE_CALL_WARNING_THRESHOLD:
            logger.warning(
                f"API 调用响应时间过长",
                extra={
                    "event": "performance_warning",
                    "warning_type": "slow_single_call",
                    "model": model,
                    "user_email": user_email,
                    "response_time": response_time,
                    "threshold": self.SINGLE_CALL_WARNING_THRESHOLD
                }
            )
        
        # 定期检查 P95 性能
        if metrics.total_calls % 100 == 0:
            self._check_p95_performance(model)
    
    def calculate_p95(self, model: Optional[str] = None) -> Optional[float]:
        """
        计算 P95 响应时间
        
        Args:
            model: 可选的模型名称，如果为 None 则计算全局 P95
            
        Returns:
            P95 响应时间（秒），如果数据不足则返回 None
        """
        if model:
            if model not in self._metrics_by_model:
                return None
            metrics = self._metrics_by_model[model]
        else:
            metrics = self._global_metrics
        
        with metrics.lock:
            if len(metrics.response_times) < 20:
                # 数据点太少，无法计算可靠的 P95
                return None
            
            # 计算 95 百分位数
            sorted_times = sorted(metrics.response_times)
            p95_index = int(len(sorted_times) * 0.95)
            return sorted_times[p95_index]
    
    def calculate_average(self, model: Optional[str] = None) -> Optional[float]:
        """
        计算平均响应时间
        
        Args:
            model: 可选的模型名称
            
        Returns:
            平均响应时间（秒）
        """
        if model:
            if model not in self._metrics_by_model:
                return None
            metrics = self._metrics_by_model[model]
        else:
            metrics = self._global_metrics
        
        with metrics.lock:
            if metrics.successful_calls == 0:
                return None
            return metrics.total_response_time / metrics.successful_calls
    
    def calculate_median(self, model: Optional[str] = None) -> Optional[float]:
        """
        计算中位数响应时间
        
        Args:
            model: 可选的模型名称
            
        Returns:
            中位数响应时间（秒）
        """
        if model:
            if model not in self._metrics_by_model:
                return None
            metrics = self._metrics_by_model[model]
        else:
            metrics = self._global_metrics
        
        with metrics.lock:
            if len(metrics.response_times) == 0:
                return None
            return statistics.median(metrics.response_times)
    
    def get_statistics(self, model: Optional[str] = None) -> Dict:
        """
        获取性能统计信息
        
        Args:
            model: 可选的模型名称
            
        Returns:
            性能统计字典
        """
        if model:
            if model not in self._metrics_by_model:
                return {}
            metrics = self._metrics_by_model[model]
        else:
            metrics = self._global_metrics
        
        with metrics.lock:
            if len(metrics.response_times) == 0:
                return {
                    "total_calls": metrics.total_calls,
                    "successful_calls": metrics.successful_calls,
                    "failed_calls": metrics.failed_calls,
                    "success_rate": 0.0
                }
            
            return {
                "total_calls": metrics.total_calls,
                "successful_calls": metrics.successful_calls,
                "failed_calls": metrics.failed_calls,
                "success_rate": metrics.successful_calls / metrics.total_calls if metrics.total_calls > 0 else 0.0,
                "average_response_time": self.calculate_average(model),
                "median_response_time": self.calculate_median(model),
                "p95_response_time": self.calculate_p95(model),
                "min_response_time": min(metrics.response_times) if metrics.response_times else None,
                "max_response_time": max(metrics.response_times) if metrics.response_times else None
            }
    
    def get_all_models_statistics(self) -> Dict[str, Dict]:
        """
        获取所有模型的性能统计
        
        Returns:
            按模型分组的性能统计字典
        """
        result = {
            "global": self.get_statistics()
        }
        
        for model in self._metrics_by_model.keys():
            result[model] = self.get_statistics(model)
        
        return result
    
    def _check_p95_performance(self, model: str) -> None:
        """
        检查 P95 性能是否超过阈值
        
        Args:
            model: 模型名称
        """
        p95 = self.calculate_p95(model)
        
        if p95 is not None and p95 > self.P95_WARNING_THRESHOLD:
            logger.warning(
                f"模型 P95 响应时间超过阈值",
                extra={
                    "event": "performance_warning",
                    "warning_type": "high_p95",
                    "model": model,
                    "p95_response_time": p95,
                    "threshold": self.P95_WARNING_THRESHOLD,
                    "statistics": self.get_statistics(model)
                }
            )
    
    def reset_metrics(self, model: Optional[str] = None) -> None:
        """
        重置性能指标
        
        Args:
            model: 可选的模型名称，如果为 None 则重置所有指标
        """
        if model:
            if model in self._metrics_by_model:
                self._metrics_by_model[model] = PerformanceMetrics()
                logger.info(f"已重置模型 {model} 的性能指标")
        else:
            self._metrics_by_model.clear()
            self._global_metrics = PerformanceMetrics()
            logger.info("已重置所有性能指标")


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()
