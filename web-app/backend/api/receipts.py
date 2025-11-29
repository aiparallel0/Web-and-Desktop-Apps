"""
Receipts API routes for managing user receipts.

Provides CRUD operations for receipts with user authentication and authorization.
"""
import logging
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, g

logger = logging.getLogger(__name__)

# Create Blueprint
receipts_bp = Blueprint('receipts', __name__, url_prefix='/api/receipts')

# Lazy imports
_db_context = None
_Receipt = None
_User = None


def _get_db_context():
    """Lazy import of database context."""
    global _db_context
    if _db_context is None:
        from database.connection import get_db_context
        _db_context = get_db_context
    return _db_context


def _get_models():
    """Lazy import of database models."""
    global _Receipt, _User
    if _Receipt is None:
        from database.models import Receipt, User
        _Receipt = Receipt
        _User = User
    return _Receipt, _User


def require_auth_simple(f):
    """Simple auth check decorator for receipts routes."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from auth.jwt_handler import verify_access_token
        
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'success': False, 'error': 'Missing authorization header'}), 401
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'success': False, 'error': 'Invalid authorization header format'}), 401
        
        token = parts[1]
        payload = verify_access_token(token)
        if not payload:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        g.user_id = payload.get('user_id')
        g.is_admin = payload.get('is_admin', False)
        
        return f(*args, **kwargs)
    
    return decorated_function


@receipts_bp.route('', methods=['GET'])
@require_auth_simple
def list_receipts():
    """
    List receipts for the current user.
    
    Query parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: 20, max: 100)
        store_name: Filter by store name
        status: Filter by status (processing, completed, failed)
        start_date: Filter by date range start (ISO format)
        end_date: Filter by date range end (ISO format)
        sort_by: Sort field (created_at, transaction_date, total_amount)
        sort_order: Sort order (asc, desc)
    
    Returns:
        200: List of receipts with pagination info
    """
    try:
        Receipt, User = _get_models()
        
        # Parse query parameters
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
        store_name = request.args.get('store_name', '').strip()
        status = request.args.get('status', '').strip()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        with _get_db_context()() as db:
            query = db.query(Receipt).filter(Receipt.user_id == g.user_id)
            
            # Apply filters
            if store_name:
                query = query.filter(Receipt.store_name.ilike(f'%{store_name}%'))
            
            if status:
                query = query.filter(Receipt.status == status)
            
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    query = query.filter(Receipt.transaction_date >= start_dt)
                except ValueError:
                    pass
            
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    query = query.filter(Receipt.transaction_date <= end_dt)
                except ValueError:
                    pass
            
            # Apply sorting
            sort_column = getattr(Receipt, sort_by, Receipt.created_at)
            if sort_order == 'asc':
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            receipts = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return jsonify({
                'success': True,
                'receipts': [
                    {
                        'id': str(r.id),
                        'filename': r.filename,
                        'store_name': r.store_name,
                        'total_amount': r.total_amount,
                        'transaction_date': r.transaction_date.isoformat() if r.transaction_date else None,
                        'model_used': r.model_used,
                        'confidence_score': r.confidence_score,
                        'status': r.status,
                        'created_at': r.created_at.isoformat() if r.created_at else None
                    }
                    for r in receipts
                ],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            })
            
    except Exception as e:
        logger.error(f"List receipts error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to list receipts'}), 500


@receipts_bp.route('/<receipt_id>', methods=['GET'])
@require_auth_simple
def get_receipt(receipt_id):
    """
    Get a specific receipt by ID.
    
    Returns:
        200: Receipt details with extracted data
        404: Receipt not found
    """
    try:
        Receipt, _ = _get_models()
        
        with _get_db_context()() as db:
            receipt = db.query(Receipt).filter(
                Receipt.id == receipt_id,
                Receipt.user_id == g.user_id
            ).first()
            
            if not receipt:
                return jsonify({'success': False, 'error': 'Receipt not found'}), 404
            
            return jsonify({
                'success': True,
                'receipt': {
                    'id': str(receipt.id),
                    'filename': receipt.filename,
                    'image_url': receipt.image_url,
                    'file_size_bytes': receipt.file_size_bytes,
                    'mime_type': receipt.mime_type,
                    'store_name': receipt.store_name,
                    'total_amount': receipt.total_amount,
                    'transaction_date': receipt.transaction_date.isoformat() if receipt.transaction_date else None,
                    'extracted_data': receipt.extracted_data,
                    'model_used': receipt.model_used,
                    'processing_time_seconds': receipt.processing_time_seconds,
                    'confidence_score': receipt.confidence_score,
                    'status': receipt.status,
                    'error_message': receipt.error_message,
                    'created_at': receipt.created_at.isoformat() if receipt.created_at else None,
                    'updated_at': receipt.updated_at.isoformat() if receipt.updated_at else None
                }
            })
            
    except Exception as e:
        logger.error(f"Get receipt error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to get receipt'}), 500


@receipts_bp.route('/<receipt_id>', methods=['DELETE'])
@require_auth_simple
def delete_receipt(receipt_id):
    """
    Delete a receipt.
    
    Returns:
        200: Receipt deleted successfully
        404: Receipt not found
    """
    try:
        Receipt, _ = _get_models()
        
        with _get_db_context()() as db:
            receipt = db.query(Receipt).filter(
                Receipt.id == receipt_id,
                Receipt.user_id == g.user_id
            ).first()
            
            if not receipt:
                return jsonify({'success': False, 'error': 'Receipt not found'}), 404
            
            db.delete(receipt)
            db.commit()
            
            logger.info(f"Receipt deleted: {receipt_id}")
            
            return jsonify({
                'success': True,
                'message': 'Receipt deleted successfully'
            })
            
    except Exception as e:
        logger.error(f"Delete receipt error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to delete receipt'}), 500


@receipts_bp.route('/<receipt_id>', methods=['PATCH'])
@require_auth_simple
def update_receipt(receipt_id):
    """
    Update receipt data (e.g., correct extracted information).
    
    Request body:
        {
            "store_name": "Updated Store Name",
            "total_amount": 25.99,
            "transaction_date": "2024-01-15",
            "extracted_data": { ... }
        }
    
    Returns:
        200: Receipt updated successfully
        404: Receipt not found
    """
    try:
        Receipt, _ = _get_models()
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Request body is required'}), 400
        
        with _get_db_context()() as db:
            receipt = db.query(Receipt).filter(
                Receipt.id == receipt_id,
                Receipt.user_id == g.user_id
            ).first()
            
            if not receipt:
                return jsonify({'success': False, 'error': 'Receipt not found'}), 404
            
            # Update allowed fields
            if 'store_name' in data:
                receipt.store_name = data['store_name']
            
            if 'total_amount' in data:
                try:
                    receipt.total_amount = float(data['total_amount'])
                except (ValueError, TypeError):
                    pass
            
            if 'transaction_date' in data:
                try:
                    receipt.transaction_date = datetime.fromisoformat(
                        data['transaction_date'].replace('Z', '+00:00')
                    )
                except ValueError:
                    pass
            
            if 'extracted_data' in data and isinstance(data['extracted_data'], dict):
                receipt.extracted_data = data['extracted_data']
            
            receipt.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Receipt updated: {receipt_id}")
            
            return jsonify({
                'success': True,
                'message': 'Receipt updated successfully',
                'receipt': {
                    'id': str(receipt.id),
                    'store_name': receipt.store_name,
                    'total_amount': receipt.total_amount,
                    'transaction_date': receipt.transaction_date.isoformat() if receipt.transaction_date else None
                }
            })
            
    except Exception as e:
        logger.error(f"Update receipt error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to update receipt'}), 500


@receipts_bp.route('/stats', methods=['GET'])
@require_auth_simple
def get_receipt_stats():
    """
    Get receipt statistics for the current user.
    
    Query parameters:
        period: Time period (month, year, all)
    
    Returns:
        200: Receipt statistics
    """
    try:
        from sqlalchemy import func
        Receipt, _ = _get_models()
        
        period = request.args.get('period', 'month')
        
        with _get_db_context()() as db:
            query = db.query(Receipt).filter(Receipt.user_id == g.user_id)
            
            # Apply time filter
            now = datetime.utcnow()
            if period == 'month':
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Receipt.created_at >= start_date)
            elif period == 'year':
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Receipt.created_at >= start_date)
            
            # Get counts
            total_count = query.count()
            completed_count = query.filter(Receipt.status == 'completed').count()
            failed_count = query.filter(Receipt.status == 'failed').count()
            
            # Get totals
            total_amount_result = db.query(func.sum(Receipt.total_amount)).filter(
                Receipt.user_id == g.user_id,
                Receipt.status == 'completed'
            )
            if period == 'month':
                total_amount_result = total_amount_result.filter(Receipt.created_at >= start_date)
            elif period == 'year':
                total_amount_result = total_amount_result.filter(Receipt.created_at >= start_date)
            
            total_amount = total_amount_result.scalar() or 0
            
            # Get top stores
            top_stores = db.query(
                Receipt.store_name,
                func.count(Receipt.id).label('count')
            ).filter(
                Receipt.user_id == g.user_id,
                Receipt.store_name.isnot(None)
            ).group_by(Receipt.store_name).order_by(
                func.count(Receipt.id).desc()
            ).limit(5).all()
            
            return jsonify({
                'success': True,
                'stats': {
                    'period': period,
                    'total_receipts': total_count,
                    'completed': completed_count,
                    'failed': failed_count,
                    'total_amount': float(total_amount),
                    'top_stores': [
                        {'store_name': s[0], 'count': s[1]} 
                        for s in top_stores if s[0]
                    ]
                }
            })
            
    except Exception as e:
        logger.error(f"Get stats error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to get statistics'}), 500


def register_receipts_routes(app):
    """Register receipts blueprint with the Flask app."""
    app.register_blueprint(receipts_bp)
    logger.info("Receipts routes registered")
