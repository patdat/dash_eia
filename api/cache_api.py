"""
Simple API endpoints for cache management
Add these to your Flask server if needed
"""
from flask import jsonify
from app import server
from src.utils.data_loader import (
    refresh_data_and_cache, 
    invalidate_data_cache, 
    get_cache_stats,
    check_data_freshness,
    preload_common_data
)


@server.route('/api/cache/stats')
def api_cache_stats():
    """API endpoint to get cache statistics"""
    try:
        stats = get_cache_stats()
        return jsonify({
            "status": "success",
            "data": {
                "total_cached_items": stats["total_cached_items"],
                "cache_keys_count": len(stats["cache_keys"]),
                "data_files": stats.get("data_files", {})
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@server.route('/api/cache/refresh', methods=['POST'])
def api_cache_refresh():
    """API endpoint to refresh cache"""
    try:
        refresh_data_and_cache()
        return jsonify({
            "status": "success",
            "message": "Cache refreshed successfully"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@server.route('/api/cache/clear', methods=['POST'])
def api_cache_clear():
    """API endpoint to clear cache"""
    try:
        invalidate_data_cache()
        return jsonify({
            "status": "success", 
            "message": "Cache cleared successfully"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@server.route('/api/data/freshness')
def api_data_freshness():
    """API endpoint to check data freshness"""
    try:
        file_info = check_data_freshness()
        
        # Convert datetime objects to strings for JSON serialization
        serializable_info = {}
        for file_path, info in file_info.items():
            serializable_info[file_path] = {
                'exists': info['exists']
            }
            if info['exists']:
                serializable_info[file_path]['last_modified'] = info['last_modified'].isoformat()
        
        return jsonify({
            "status": "success",
            "data": serializable_info
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
