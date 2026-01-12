"""
Pando Core Systems Integration

Main integration point for all Pando core systems.
Provides unified access to:
- Decision engine (autonomy)
- Task management
- Async communication
- Repository management
- Terminal coordination
"""

import logging
from typing import Optional, Dict
from .autonomy_engine import AutonomyEngine, DecisionType
from .task_system import TaskSystem, TaskCategory, TaskStatus
from .async_comm import AsyncCommunicationSystem, BlockingLevel
from .repo_manager import RepositoryManager

logger = logging.getLogger(__name__)


class PandoCore:
    """
    Main Pando system orchestrator.
    
    Coordinates all subsystems:
    - Makes autonomous decisions
    - Manages task queue
    - Handles user communication
    - Manages repositories
    """
    
    def __init__(
        self,
        dev_root: str = "c:\\Users\\jake\\dev",
        decisions_file: str = "pando_decisions.json",
        tasks_file: str = "pando_tasks.jsonl",
        questions_file: str = "pando_questions.jsonl",
        responses_file: str = "pando_responses.jsonl",
        repos_file: str = "pando_repos.json",
    ):
        """Initialize all core systems"""
        self.autonomy = AutonomyEngine(decisions_file)
        self.tasks = TaskSystem(tasks_file)
        self.communication = AsyncCommunicationSystem(questions_file, responses_file)
        self.repos = RepositoryManager(dev_root, repos_file)
        
        logger.info("Pando Core initialized")
    
    def evaluate_and_assign_task(
        self,
        task_description: str,
        category: TaskCategory = TaskCategory.PRIMARY,
        estimated_minutes: float = 60,
        priority: float = 0.5,
    ) -> str:
        """
        Main entry point: evaluate task and decide how to handle it.
        
        Flow:
        1. Create task
        2. Evaluate with decision engine
        3. Execute decision (EXECUTE, PROPOSE, BRANCH, ASK, ESCALATE)
        4. Return task ID and decision type
        
        Returns:
            Task ID
        """
        # Create task
        task = self.tasks.create_task(
            description=task_description,
            category=category,
            estimated_minutes=estimated_minutes,
            priority=priority,
        )
        
        logger.info(f"Created task {task.id}: {task_description[:50]}...")
        
        return task.id
    
    def process_task(
        self,
        task_id: str,
        terminal: int = 1,
    ) -> Optional[dict]:
        """
        Process a task: evaluate and execute based on confidence.
        
        Returns:
            Decision details or None
        """
        task = self.tasks.tasks.get(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return None
        
        # Evaluate task
        decision = self.autonomy.evaluate_task(
            task_id=task_id,
            task_description=task.description,
            prerequisites={
                "is_well_specified": True,
                "has_tests": False,
                "framework_chosen": False,
            },
            estimated_complexity=0.5,
            resource_available={
                "gpu_memory_gb": 6.5,
                "ram_gb": 12,
                "time_minutes": 240,
                "free_terminals": 4,
            }
        )
        
        logger.info(f"Decision for {task_id}: {decision.decision_type.value} "
                   f"(confidence: {decision.confidence:.1%})")
        
        # Execute decision
        if decision.decision_type == DecisionType.EXECUTE:
            self.tasks.assign_task_to_terminal(task_id, terminal)
            logger.info(f"Executing {task_id} on terminal {terminal}")
        
        elif decision.decision_type == DecisionType.PROPOSE:
            # Create branch and propose
            branch = self.repos.create_branch(
                "pando-dev",
                "feature",
                task.description[:20]
            )
            task.branch_name = branch
            logger.info(f"Proposed {task_id} on branch {branch}")
            self.tasks.tasks[task_id].status = TaskStatus.BLOCKED
        
        elif decision.decision_type == DecisionType.BRANCH:
            # Create assumption branch
            branch = self.repos.create_branch(
                "pando-dev",
                "assume",
                task.description[:20]
            )
            task.branch_name = branch
            
            # Pose question about assumptions
            question = self.communication.pose_question(
                task_id=task_id,
                category="approach_choice",
                question_text=f"Should we use the approach I'm about to try?",
                context=f"I'm working on: {task.description}",
                options=list(decision.alternatives_rejected) + ["Continue with my approach"],
                blocking_level=BlockingLevel.NON_BLOCKING,
                assumed_answer=decision.selected_approach,
                branch_name=branch,
            )
            
            self.tasks.assign_task_to_terminal(task_id, terminal)
            logger.info(f"Branching {task_id} on {branch} with assumption Q: {question.id}")
        
        elif decision.decision_type == DecisionType.ASK:
            # Blocking question
            question = self.communication.pose_question(
                task_id=task_id,
                category="blocking_decision",
                question_text="How should I approach this task?",
                context=f"Task: {task.description}",
                options=decision.alternatives_rejected,
                blocking_level=BlockingLevel.BLOCKING,
                branch_name=None,  # No branch yet
            )
            
            self.tasks.tasks[task_id].status = TaskStatus.BLOCKED
            self.tasks.tasks[task_id].blocking_questions.append(question.id)
            logger.info(f"Blocking question posed for {task_id}: {question.id}")
        
        elif decision.decision_type == DecisionType.ESCALATE:
            # Critical escalation
            logger.critical(f"ESCALATION: {task_id} - {decision.reasoning}")
            self.tasks.tasks[task_id].status = TaskStatus.BLOCKED
        
        return {
            'task_id': task_id,
            'decision_type': decision.decision_type.value,
            'confidence': decision.confidence,
            'reasoning': decision.reasoning,
            'branch': task.branch_name,
        }
    
    def check_for_user_responses(self) -> Dict:
        """
        Check if user has responded to any questions.
        Process responses and update branching/work.
        
        Returns:
            Summary of responses processed
        """
        responses = self.communication.check_for_responses()
        processed = 0
        
        for q_id, response in responses:
            question = self.communication.questions[q_id]
            
            logger.info(f"Processing response to {q_id}: {response}")
            
            # Update task if applicable
            if question.task_id in self.tasks.tasks:
                task = self.tasks.tasks[question.task_id]
                task.blocking_questions.remove(q_id)
                
                if task.status == TaskStatus.BLOCKED and not task.blocking_questions:
                    task.status = TaskStatus.PENDING
                    logger.info(f"Unblocked task {task.id}")
            
            self.communication.questions[q_id].mark_resolved()
            processed += 1
        
        return {
            'responses_processed': processed,
            'pending_questions': len(self.communication.get_pending_questions()),
            'blocking_questions': len(self.communication.get_blocking_questions()),
        }
    
    def get_system_status(self) -> Dict:
        """
        Get overall system status for dashboard.
        
        Returns:
            Status summary
        """
        task_stats = self.tasks.get_statistics()
        comm_stats = self.communication.get_stats()
        
        return {
            'tasks': task_stats,
            'communication': comm_stats,
            'repositories': len(self.repos.repositories),
            'decision_quality': self.autonomy.get_calibration_score(),
        }
    
    def get_next_work_item(self) -> Optional[Dict]:
        """
        Determine what Pando should work on next.
        
        Returns:
            Next task/work item details or None
        """
        # Check for blocking questions
        blocking = self.communication.get_blocking_questions()
        if blocking:
            return {
                'type': 'waiting_for_user',
                'items': [q.question_text for q in blocking],
                'note': 'Cannot proceed until user responds',
            }
        
        # Get next task
        task = self.tasks.get_next_task()
        if task:
            return {
                'type': 'task',
                'task_id': task.id,
                'description': task.description,
                'priority': task.priority,
                'estimated_minutes': task.estimated_minutes,
            }
        
        # No work - check for self-improvement opportunities
        return {
            'type': 'idle',
            'action': 'Scan for improvement opportunities and maintenance tasks',
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    pando = PandoCore()
    
    # Create and process a task
    task_id = pando.evaluate_and_assign_task(
        "Implement JWT authentication with refresh tokens",
        TaskCategory.PRIMARY,
        estimated_minutes=120,
        priority=0.95,
    )
    
    result = pando.process_task(task_id, terminal=1)
    print(f"\nTask processing result: {result}")
    
    # Get system status
    status = pando.get_system_status()
    print(f"\nSystem status: {status}")
