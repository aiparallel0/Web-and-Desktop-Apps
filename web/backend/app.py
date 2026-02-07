from flask import jsonify

# Assuming check_database_health() is imported from database.py

@app.route('/api/database/health', methods=['GET'])
def database_health():
    health_info = check_database_health()  # Call the function to get health info
    return jsonify({
        'status': health_info['status'],
        'available_pool_connections': health_info['available_pool_connections'],
        'query_latency': health_info['query_latency'],
    })
