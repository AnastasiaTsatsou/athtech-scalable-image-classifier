"""
Performance profiling utilities for image classification
"""

import cProfile
import pstats
import time
from typing import Any, Dict
import logging

try:
    from torch.profiler import profile, ProfilerActivity

    TORCH_PROFILER_AVAILABLE = True
except ImportError:
    TORCH_PROFILER_AVAILABLE = False

logger = logging.getLogger(__name__)


def profile_inference(
    classifier, image, iterations: int = 100
) -> Dict[str, Any]:
    """
    Profile inference performance using both Python and PyTorch profilers

    Args:
        classifier: The classifier instance
        image: PIL Image to classify
        iterations: Number of iterations for profiling

    Returns:
        Dictionary with profiling results
    """
    results = {}

    # Python profiler
    logger.info(f"Running Python profiler for {iterations} iterations...")
    profiler = cProfile.Profile()
    profiler.enable()

    start_time = time.time()
    for _ in range(iterations):
        classifier.predict(image, top_k=5)
    end_time = time.time()

    profiler.disable()

    # Get Python profiler stats
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumulative")

    # Extract top functions
    top_functions = []
    for func, (cc, nc, tt, ct, callers) in stats.stats.items():
        top_functions.append(
            {
                "function": f"{func[0]}:{func[1]}({func[2]})",
                "cumulative_time": ct,
                "total_time": tt,
                "calls": cc,
            }
        )

    results["python_profiler"] = {
        "total_time": end_time - start_time,
        "iterations": iterations,
        "avg_time_per_iteration": (end_time - start_time) / iterations,
        "top_functions": sorted(
            top_functions, key=lambda x: x["cumulative_time"], reverse=True
        )[:10],
    }

    # PyTorch profiler (if available)
    if TORCH_PROFILER_AVAILABLE:
        logger.info("Running PyTorch profiler...")
        try:
            with profile(
                activities=[ProfilerActivity.CPU], record_shapes=True
            ) as prof:
                classifier.predict(image, top_k=5)

            # Get PyTorch profiler results
            key_averages = prof.key_averages()
            torch_results = []

            for item in key_averages:
                torch_results.append(
                    {
                        "name": item.key,
                        "cpu_time_total": item.cpu_time_total,
                        "cpu_time": item.cpu_time,
                        "count": item.count,
                        "cpu_memory_usage": item.cpu_memory_usage,
                    }
                )

            results["torch_profiler"] = {
                "top_operations": sorted(
                    torch_results,
                    key=lambda x: x["cpu_time_total"],
                    reverse=True,
                )[:10]
            }

        except Exception as e:
            logger.warning(f"PyTorch profiler failed: {e}")
            results["torch_profiler"] = {"error": str(e)}
    else:
        results["torch_profiler"] = {"error": "PyTorch profiler not available"}

    return results


def benchmark_model_performance(
    classifier, test_images, iterations: int = 10
) -> Dict[str, Any]:
    """
    Benchmark model performance across different image sizes

    Args:
        classifier: The classifier instance
        test_images: List of PIL Images of different sizes
        iterations: Number of iterations per image

    Returns:
        Dictionary with benchmark results
    """
    results = {}

    for i, image in enumerate(test_images):
        logger.info(
            f"Benchmarking image {i+1}/{len(test_images)} (size: {image.size})"
        )

        times = []
        for _ in range(iterations):
            start = time.time()
            classifier.predict(image, top_k=5)
            end = time.time()
            times.append((end - start) * 1000)  # Convert to ms

        results[f"image_{i+1}"] = {
            "size": image.size,
            "times_ms": times,
            "avg_time_ms": sum(times) / len(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "iterations": iterations,
        }

    return results


def print_profiling_summary(results: Dict[str, Any]) -> None:
    """Print a formatted summary of profiling results"""
    print("\n" + "=" * 60)
    print("PERFORMANCE PROFILING SUMMARY")
    print("=" * 60)

    # Python profiler results
    if "python_profiler" in results:
        py_prof = results["python_profiler"]
        print(
            f"\nPython Profiler Results ({py_prof['iterations']} iterations):"
        )
        print(f"Total Time: {py_prof['total_time']:.3f}s")
        print(
            f"Average per iteration: {py_prof['avg_time_per_iteration']*1000:.1f}ms"
        )

        print("\nTop Functions by Cumulative Time:")
        for i, func in enumerate(py_prof["top_functions"][:5], 1):
            print(f"{i:2d}. {func['function']}")
            print(
                f"    Cumulative: {func['cumulative_time']:.3f}s, Total: {func['total_time']:.3f}s, Calls: {func['calls']}"
            )

    # PyTorch profiler results
    if (
        "torch_profiler" in results
        and "error" not in results["torch_profiler"]
    ):
        torch_prof = results["torch_profiler"]
        print("\nPyTorch Profiler Results:")
        print("Top Operations by CPU Time:")
        for i, op in enumerate(torch_prof["top_operations"][:5], 1):
            print(f"{i:2d}. {op['name']}")
            print(
                f"    CPU Time: {op['cpu_time_total']:.3f}ms, Count: {op['count']}"
            )

    print("=" * 60)
