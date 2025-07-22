#!/usr/bin/env python3
"""
Atlas Infrastructure MCP Server
Exposes Atlas storage and infrastructure capabilities via Model Context Protocol (MCP)
Professional-grade infrastructure management and storage optimization tools
"""

from fastmcp import FastMCP
import os
import shutil
import psutil
from pathlib import Path
import json
import time
from typing import Dict, List, Any
import subprocess

mcp = FastMCP("Atlas Infrastructure", version="1.0.0")

@mcp.tool()
def analyze_disk_usage(path: str = "/") -> dict:
    """
    Analyze disk usage for a given path with detailed statistics
    
    Args:
        path: File system path to analyze (default: root)
        
    Returns:
        Comprehensive disk usage analysis including space breakdown and recommendations
    """
    try:
        # Resolve path for Windows/Unix compatibility
        if os.name == 'nt' and path == "/":
            path = "C:\\"
        
        path_obj = Path(path)
        if not path_obj.exists():
            return {"error": f"Path {path} does not exist"}
        
        # Get disk usage
        usage = shutil.disk_usage(path)
        
        # Additional analysis
        total_gb = round(usage.total / (1024**3), 2)
        used_gb = round(usage.used / (1024**3), 2)
        free_gb = round(usage.free / (1024**3), 2)
        usage_percent = round((usage.used / usage.total) * 100, 2)
        
        # Health assessment
        health_status = "healthy"
        if usage_percent > 90:
            health_status = "critical"
        elif usage_percent > 80:
            health_status = "warning"
        elif usage_percent > 70:
            health_status = "concern"
            
        recommendations = []
        if usage_percent > 80:
            recommendations.append("Consider cleanup operations")
        if usage_percent > 90:
            recommendations.append("Immediate attention required - disk nearly full")
        if free_gb < 1:
            recommendations.append("Critical: Less than 1GB free space")
        
        return {
            "path": str(path),
            "total_gb": total_gb,
            "used_gb": used_gb, 
            "free_gb": free_gb,
            "usage_percent": usage_percent,
            "health_status": health_status,
            "recommendations": recommendations,
            "analysis_timestamp": time.time()
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_system_stats() -> dict:
    """
    Get comprehensive real-time system performance statistics
    
    Returns:
        Detailed system metrics including CPU, memory, disk I/O, and network stats
    """
    try:
        stats = {
            "timestamp": time.time(),
            "cpu": {
                "usage_percent": psutil.cpu_percent(interval=1),
                "count_logical": psutil.cpu_count(),
                "count_physical": psutil.cpu_count(logical=False),
            },
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "used_percent": psutil.virtual_memory().percent,
                "free_percent": round(100 - psutil.virtual_memory().percent, 2)
            }
        }
        
        # Add load average on Unix systems
        if hasattr(os, 'getloadavg'):
            load = os.getloadavg()
            stats["load_average"] = {
                "1min": load[0],
                "5min": load[1], 
                "15min": load[2]
            }
        
        # Add disk I/O stats if available
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                stats["disk_io"] = {
                    "read_mb": round(disk_io.read_bytes / (1024**2), 2),
                    "write_mb": round(disk_io.write_bytes / (1024**2), 2),
                    "read_count": disk_io.read_count,
                    "write_count": disk_io.write_count
                }
        except:
            stats["disk_io"] = {"status": "unavailable"}
        
        # Add network I/O stats if available  
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                stats["network_io"] = {
                    "sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                    "recv_mb": round(net_io.bytes_recv / (1024**2), 2),
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                }
        except:
            stats["network_io"] = {"status": "unavailable"}
        
        # System health assessment
        health_issues = []
        if stats["cpu"]["usage_percent"] > 90:
            health_issues.append("High CPU usage")
        if stats["memory"]["used_percent"] > 90:
            health_issues.append("High memory usage")
        
        stats["health_status"] = "healthy" if not health_issues else "attention_needed"
        stats["health_issues"] = health_issues
        
        return stats
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def find_large_files(directory: str, min_size_mb: int = 100, max_results: int = 20) -> dict:
    """
    Find and analyze large files in a directory tree
    
    Args:
        directory: Directory to search in
        min_size_mb: Minimum file size in MB to include (default: 100)
        max_results: Maximum number of results to return (default: 20)
        
    Returns:
        List of large files with detailed analysis and cleanup suggestions
    """
    try:
        large_files = []
        min_size_bytes = min_size_mb * 1024 * 1024
        total_large_size = 0
        
        # Security check - don't scan system directories on Windows
        if os.name == 'nt':
            restricted_dirs = ['windows', 'program files', 'program files (x86)', '$recycle.bin']
            dir_lower = directory.lower()
            for restricted in restricted_dirs:
                if restricted in dir_lower:
                    return {"error": f"Cannot scan system directory: {directory}"}
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    if size > min_size_bytes:
                        modified_time = os.path.getmtime(file_path)
                        age_days = round((time.time() - modified_time) / 86400, 1)
                        
                        # File type analysis
                        extension = Path(file_path).suffix.lower()
                        file_type = "other"
                        if extension in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']:
                            file_type = "video"
                        elif extension in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                            file_type = "archive"
                        elif extension in ['.log', '.txt']:
                            file_type = "log"
                        elif extension in ['.jpg', '.png', '.bmp', '.gif', '.tiff']:
                            file_type = "image"
                        elif extension in ['.pdf', '.doc', '.docx']:
                            file_type = "document"
                        
                        large_files.append({
                            "path": file_path,
                            "size_mb": round(size / (1024**2), 2),
                            "age_days": age_days,
                            "extension": extension,
                            "file_type": file_type,
                            "last_modified": time.ctime(modified_time)
                        })
                        total_large_size += size
                        
                        # Stop if we have enough results
                        if len(large_files) >= max_results * 2:  # Get extra to sort later
                            break
                except (OSError, IOError):
                    continue
                    
            if len(large_files) >= max_results * 2:
                break
        
        # Sort by size descending and limit results
        large_files.sort(key=lambda x: x["size_mb"], reverse=True)
        large_files = large_files[:max_results]
        
        # Generate recommendations
        recommendations = []
        if total_large_size > 1024**3:  # > 1GB
            recommendations.append("Consider archiving or compressing old large files")
        
        video_files = [f for f in large_files if f["file_type"] == "video"]
        if video_files:
            recommendations.append(f"Found {len(video_files)} large video files - consider compression")
        
        old_files = [f for f in large_files if f["age_days"] > 365]
        if old_files:
            recommendations.append(f"Found {len(old_files)} files older than 1 year")
        
        return {
            "directory": directory,
            "min_size_mb": min_size_mb,
            "files_found": len(large_files),
            "total_size_gb": round(total_large_size / (1024**3), 2),
            "files": large_files,
            "recommendations": recommendations,
            "scan_timestamp": time.time()
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def cleanup_recommendations(path: str, deep_analysis: bool = False) -> dict:
    """
    Provide intelligent cleanup recommendations for a path
    
    Args:
        path: Path to analyze for cleanup opportunities
        deep_analysis: Perform deeper analysis (slower but more thorough)
        
    Returns:
        Detailed cleanup recommendations with potential space savings
    """
    try:
        recommendations = []
        potential_savings_mb = 0
        
        # Check for common cleanup targets
        temp_dirs = ["tmp", "temp", "__pycache__", ".cache", "node_modules", "Temp"]
        log_extensions = [".log", ".tmp", ".bak", ".old"]
        
        for root, dirs, files in os.walk(path):
            # Limit depth for performance unless deep analysis requested
            depth = root[len(path):].count(os.sep)
            if not deep_analysis and depth > 3:
                continue
                
            # Check for temp directories
            for dir_name in dirs[:]:  # Copy list to modify while iterating
                if dir_name.lower() in [t.lower() for t in temp_dirs]:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        size = 0
                        file_count = 0
                        for dp, dn, fn in os.walk(dir_path):
                            for f in fn:
                                try:
                                    size += os.path.getsize(os.path.join(dp, f))
                                    file_count += 1
                                except (OSError, IOError):
                                    continue
                                    
                        if size > 1024 * 1024:  # > 1MB
                            size_mb = round(size / (1024**2), 2)
                            recommendations.append({
                                "type": "temp_directory",
                                "path": dir_path,
                                "size_mb": size_mb,
                                "file_count": file_count,
                                "action": "safe_to_delete",
                                "risk_level": "low"
                            })
                            potential_savings_mb += size_mb
                            
                        # Don't recurse into temp directories
                        dirs.remove(dir_name)
                    except (OSError, IOError):
                        continue
            
            # Check for cleanup-worthy files
            for file in files:
                file_path = os.path.join(root, file)
                file_lower = file.lower()
                
                try:
                    size = os.path.getsize(file_path)
                    age_days = round((time.time() - os.path.getmtime(file_path)) / 86400, 1)
                    
                    # Log files
                    if any(file_lower.endswith(ext) for ext in log_extensions):
                        if size > 10 * 1024 * 1024:  # > 10MB
                            size_mb = round(size / (1024**2), 2)
                            recommendations.append({
                                "type": "log_file",
                                "path": file_path,
                                "size_mb": size_mb,
                                "age_days": age_days,
                                "action": "consider_truncating_or_compressing",
                                "risk_level": "medium"
                            })
                            potential_savings_mb += size_mb * 0.8  # Assume 80% compression
                    
                    # Duplicate file detection (basic)
                    if deep_analysis and size > 1024 * 1024:  # Only for files > 1MB
                        # This is a simplified duplicate check - in production you'd use checksums
                        base_name = os.path.splitext(file)[0]
                        if any(base_name in f for f in files if f != file):
                            size_mb = round(size / (1024**2), 2)
                            recommendations.append({
                                "type": "potential_duplicate",
                                "path": file_path,
                                "size_mb": size_mb,
                                "action": "manual_review_needed",
                                "risk_level": "high"
                            })
                    
                except (OSError, IOError):
                    continue
        
        # Sort recommendations by potential space savings
        recommendations.sort(key=lambda x: x.get("size_mb", 0), reverse=True)
        
        # Generate summary insights
        insights = []
        if potential_savings_mb > 1000:  # > 1GB
            insights.append(f"Significant cleanup potential: {round(potential_savings_mb/1024, 1)}GB could be recovered")
        
        temp_recs = [r for r in recommendations if r["type"] == "temp_directory"]
        if temp_recs:
            insights.append(f"Found {len(temp_recs)} temporary directories safe for cleanup")
        
        log_recs = [r for r in recommendations if r["type"] == "log_file"]
        if log_recs:
            insights.append(f"Found {len(log_recs)} large log files that could be compressed")
        
        return {
            "path": path,
            "analysis_type": "deep" if deep_analysis else "standard",
            "recommendations_count": len(recommendations),
            "recommendations": recommendations[:20],  # Limit to top 20
            "potential_savings_mb": round(potential_savings_mb, 2),
            "potential_savings_gb": round(potential_savings_mb / 1024, 2),
            "insights": insights,
            "scan_timestamp": time.time()
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def system_health_check() -> dict:
    """
    Comprehensive system health assessment combining multiple metrics
    
    Returns:
        Overall system health report with actionable recommendations
    """
    try:
        # Get basic system stats
        system_stats = get_system_stats()
        
        # Analyze disk usage for all available drives
        disk_analysis = []
        if os.name == 'nt':  # Windows
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    analysis = analyze_disk_usage(drive)
                    if "error" not in analysis:
                        disk_analysis.append(analysis)
        else:  # Unix-like
            for mount_point in ['/', '/home', '/var', '/tmp']:
                if os.path.exists(mount_point):
                    analysis = analyze_disk_usage(mount_point)
                    if "error" not in analysis:
                        disk_analysis.append(analysis)
        
        # Overall health assessment
        health_score = 100
        issues = []
        recommendations = []
        
        # CPU health
        if "error" not in system_stats:
            cpu_usage = system_stats.get("cpu", {}).get("usage_percent", 0)
            if cpu_usage > 90:
                health_score -= 20
                issues.append("High CPU usage")
                recommendations.append("Investigate high CPU processes")
            elif cpu_usage > 70:
                health_score -= 10
                issues.append("Elevated CPU usage")
        
        # Memory health
        if "error" not in system_stats:
            memory_usage = system_stats.get("memory", {}).get("used_percent", 0)
            if memory_usage > 90:
                health_score -= 25
                issues.append("Critical memory usage")
                recommendations.append("Close unnecessary applications or add more RAM")
            elif memory_usage > 80:
                health_score -= 15
                issues.append("High memory usage")
        
        # Disk health
        critical_disks = [d for d in disk_analysis if d.get("usage_percent", 0) > 90]
        warning_disks = [d for d in disk_analysis if d.get("usage_percent", 0) > 80]
        
        if critical_disks:
            health_score -= 30
            issues.append(f"Critical disk space on {len(critical_disks)} drives")
            recommendations.append("Immediate cleanup required for critical drives")
        elif warning_disks:
            health_score -= 15
            issues.append(f"Low disk space on {len(warning_disks)} drives")
            recommendations.append("Consider cleanup operations")
        
        # Determine overall status
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 70:
            status = "good"
        elif health_score >= 50:
            status = "fair"
        elif health_score >= 30:
            status = "poor"
        else:
            status = "critical"
        
        return {
            "health_score": health_score,
            "status": status,
            "issues": issues,
            "recommendations": recommendations,
            "system_stats": system_stats,
            "disk_analysis": disk_analysis,
            "check_timestamp": time.time(),
            "summary": f"System health: {status.upper()} ({health_score}/100)"
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting Atlas Infrastructure MCP Server...")
    print("🔧 Professional infrastructure management tools ready")
    print("💼 Revenue model: $0.005 per API call")
    print("🌐 Server will be available for Smithery AI integration")
    mcp.run() 