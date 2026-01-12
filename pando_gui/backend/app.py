"""
Pando Flask Backend

REST API and WebSocket server for GUI dashboard.
Handles:
- Task management endpoints
- Question/response handling
- Real-time updates via WebSocket
- Repository status
- System metrics
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import logging
import json
from datetime import datetime
from typing import Dict, Any
import os

# Import Pando core
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pando_core import PandoCore
from pando_core.task_system import TaskCategory, TaskStatus
from pando_core.async_comm import BlockingLevel
from pando_core.direction_api import get_direction_api

logger = logging.getLogger(__name__)

# Configure logging to see errors
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)

# Try to initialize Pando core, with fallback
try:
    pando = PandoCore()
    logger.info("PandoCore initialized successfully")
except Exception as e:
    logger.warning(f"Could not initialize PandoCore: {e}. API will operate in degraded mode.")
    pando = None

# Initialize Flask app
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Connected clients for WebSocket
connected_clients = set()


# ============================================================================
# REST API ENDPOINTS
# ============================================================================

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current system status"""
    try:
        status = pando.get_system_status()
        work_item = pando.get_next_work_item()
        
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'system': status,
            'next_work': work_item,
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    try:
        tasks = [
            {
                'id': t.id,
                'description': t.description,
                'category': t.category.value,
                'status': t.status.value,
                'priority': t.priority,
                'estimated_minutes': t.estimated_minutes,
                'progress': pando.tasks._estimate_progress(t),
                'assigned_terminal': t.assigned_terminal,
            }
            for t in pando.tasks.tasks.values()
        ]
        
        return jsonify({
            'status': 'ok',
            'tasks': tasks,
            'count': len(tasks),
        })
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    try:
        data = request.json
        
        task_id = pando.evaluate_and_assign_task(
            task_description=data.get('description', ''),
            category=TaskCategory(data.get('category', 'PRIMARY')),
            estimated_minutes=float(data.get('estimated_minutes', 60)),
            priority=float(data.get('priority', 0.5)),
        )
        
        # Process the task
        result = pando.process_task(task_id)
        
        return jsonify({
            'status': 'ok',
            'task_id': task_id,
            'decision': result,
        })
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """Get details of a specific task"""
    try:
        status = pando.tasks.get_task_status(task_id)
        if not status:
            return jsonify({'status': 'error', 'message': 'Task not found'}), 404
        
        return jsonify({
            'status': 'ok',
            'task': status,
        })
    except Exception as e:
        logger.error(f"Error getting task: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/questions', methods=['GET'])
def get_questions():
    """Get pending questions for user"""
    try:
        questions = pando.communication.get_pending_questions()
        
        return jsonify({
            'status': 'ok',
            'questions': [
                {
                    'id': q.id,
                    'question': q.question_text,
                    'context': q.context,
                    'options': q.options,
                    'assumed_answer': q.assumed_answer if q.blocking_level == BlockingLevel.NON_BLOCKING else None,
                    'blocking': q.blocking_level == BlockingLevel.BLOCKING,
                    'task_id': q.task_id,
                    'branch': q.branch_name,
                }
                for q in questions
            ],
            'count': len(questions),
        })
    except Exception as e:
        logger.error(f"Error getting questions: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/questions/<question_id>', methods=['POST'])
def answer_question(question_id):
    """User answers a question"""
    try:
        data = request.json
        response = data.get('response', '')
        
        pando.communication.record_response(question_id, response)
        
        # Check if this unblocks any tasks
        pando.check_for_user_responses()
        
        # Broadcast update to all clients
        socketio.emit('question_answered', {
            'question_id': question_id,
            'response': response,
        }, broadcast=True)
        
        return jsonify({
            'status': 'ok',
            'message': 'Response recorded',
        })
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/repos', methods=['GET'])
def get_repos():
    """Get repository status"""
    try:
        repos = pando.repos.get_all_repos()
        
        return jsonify({
            'status': 'ok',
            'repositories': repos,
            'count': len(repos),
        })
    except Exception as e:
        logger.error(f"Error getting repos: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get system performance metrics"""
    try:
        task_stats = pando.tasks.get_statistics()
        comm_stats = pando.communication.get_stats()
        
        return jsonify({
            'status': 'ok',
            'tasks': task_stats,
            'communication': comm_stats,
            'decision_quality': pando.autonomy.get_calibration_score(),
            'timestamp': datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Client connected to WebSocket"""
    connected_clients.add(request.sid)
    logger.info(f"Client connected: {request.sid} (total: {len(connected_clients)})")
    
    # Send initial status
    try:
        status = pando.get_system_status()
        emit('initial_status', {
            'system': status,
            'timestamp': datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error sending initial status: {e}")


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected from WebSocket"""
    connected_clients.discard(request.sid)
    logger.info(f"Client disconnected: {request.sid} (total: {len(connected_clients)})")


@socketio.on('request_status_update')
def handle_status_update():
    """Client requested status update"""
    try:
        status = pando.get_system_status()
        emit('status_update', {
            'system': status,
            'timestamp': datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error sending status update: {e}")


@socketio.on('request_tasks_update')
def handle_tasks_update():
    """Client requested task list update"""
    try:
        tasks = [
            {
                'id': t.id,
                'description': t.description,
                'category': t.category.value,
                'status': t.status.value,
                'priority': t.priority,
                'progress': pando.tasks._estimate_progress(t),
            }
            for t in pando.tasks.tasks.values()
        ]
        
        emit('tasks_update', {
            'tasks': tasks,
            'count': len(tasks),
            'timestamp': datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error sending tasks update: {e}")


def broadcast_update(event_type: str, data: Dict[str, Any]):
    """
    Broadcast an update to all connected clients.
    
    Called by Pando when something changes that affects the UI.
    """
    socketio.emit(event_type, {
        **data,
        'timestamp': datetime.now().isoformat(),
    }, broadcast=True)


# ============================================================================
# Health check
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'connected_clients': len(connected_clients),
    })


# ============================================================================
# DIRECTIONS API - User-facing task submission system
# ============================================================================

@app.route('/api/directions', methods=['POST'])
def submit_direction():
    """Submit a new direction (high-level task description)"""
    try:
        data = request.get_json()
        direction_api = get_direction_api()
        
        text = data.get('text', '').strip()
        priority = data.get('priority', 'medium').lower()
        deadline = data.get('deadline')
        context = data.get('context')
        
        if not text:
            return jsonify({'error': 'Direction text required'}), 400
        
        # Submit direction
        direction = direction_api.submit_direction(
            text=text,
            priority=priority,
            deadline=deadline,
            context=context
        )
        
        # Parse into tasks
        tasks = direction_api.parse_direction_into_tasks(text)
        
        # Create actual tasks in task system
        task_ids = []
        for i, task_info in enumerate(tasks):
            pando_task = pando.task_system.create_task(
                category=TaskCategory.ENGINEERING,
                title=task_info['title'],
                description=f"Part of direction: {text}",
                priority_level=2 if task_info['priority'] == 'high' else 1,
                estimated_minutes=task_info.get('estimated_minutes', 60)
            )
            task_ids.append(pando_task['id'])
        
        return jsonify({
            'direction_id': direction['direction_id'],
            'text': text,
            'priority': priority,
            'status': direction['status'],
            'tasks_created': len(tasks),
            'task_ids': task_ids,
            'created_at': direction['created_at']
        }), 201
        
    except Exception as e:
        logger.error(f"Error submitting direction: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/directions', methods=['GET'])
def get_directions():
    """Get all directions"""
    try:
        direction_api = get_direction_api()
        status = request.args.get('status')
        priority = request.args.get('priority')
        
        directions = direction_api.get_directions(status=status, priority=priority)
        
        return jsonify({
            'total': len(directions),
            'directions': directions
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting directions: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/directions/<direction_id>', methods=['GET'])
def get_direction(direction_id):
    """Get a specific direction"""
    try:
        direction_api = get_direction_api()
        direction = direction_api.get_direction(direction_id)
        
        if not direction:
            return jsonify({'error': 'Direction not found'}), 404
        
        return jsonify(direction), 200
        
    except Exception as e:
        logger.error(f"Error getting direction: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/directions/stats', methods=['GET'])
def get_directions_stats():
    """Get direction statistics"""
    try:
        direction_api = get_direction_api()
        stats = direction_api.get_stats()
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Error handlers
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'status': 'error', 'message': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ============================================================================
# Main entry point
# ============================================================================

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting Pando Flask backend on http://127.0.0.1:5000")
    
    # Run with SocketIO support
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)
