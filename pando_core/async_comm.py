"""
Async User Communication System

Handles non-blocking user interaction with Pando.
- User questions don't block Pando's work
- Pando can make assumptions and continue
- Responses integrated when received
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class QuestionStatus(Enum):
    """Lifecycle of a user question"""
    PENDING = "PENDING"      # Awaiting user response
    ANSWERED = "ANSWERED"    # User responded
    RESOLVED = "RESOLVED"    # Response integrated into work
    DEFERRED = "DEFERRED"    # User chose to decide later
    CANCELLED = "CANCELLED"  # No longer relevant


class BlockingLevel(Enum):
    """How critical is this question?"""
    BLOCKING = "BLOCKING"        # Cannot proceed without answer
    NON_BLOCKING = "NON_BLOCKING"  # Can continue with assumption
    INFORMATIONAL = "INFORMATIONAL"  # Just FYI


@dataclass
class Question:
    """Represents a question posed to the user"""
    id: str
    timestamp: str
    task_id: str
    category: str  # e.g., "technical_choice", "confirmation", "clarification"
    question_text: str
    context: str  # Why this question matters
    blocking_level: BlockingLevel
    assumed_answer: Optional[str]  # For NON_BLOCKING questions
    deadline: Optional[str]  # ISO timestamp when user should respond
    status: QuestionStatus
    options: List[str]  # Possible responses
    user_response: Optional[str] = None
    user_response_timestamp: Optional[str] = None
    branch_name: Optional[str] = None  # Branch this question applies to
    
    def mark_answered(self, response: str):
        """User has responded"""
        self.status = QuestionStatus.ANSWERED
        self.user_response = response
        self.user_response_timestamp = datetime.now().isoformat()
    
    def mark_resolved(self):
        """Response has been integrated into work"""
        self.status = QuestionStatus.RESOLVED
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        return {
            **asdict(self),
            'blocking_level': self.blocking_level.value,
            'status': self.status.value,
        }


@dataclass
class ProposalResponse:
    """User response to a Pando proposal"""
    id: str
    proposal_id: str
    response_type: str  # "approve", "modify", "reject"
    reason: Optional[str]
    suggestions: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class AsyncCommunicationSystem:
    """
    Non-blocking communication system.
    
    Allows:
    - Pando to pose questions
    - Pando to make assumptions and continue work
    - User to respond when ready
    - Seamless integration of responses
    """
    
    def __init__(
        self,
        questions_file: str = "pando_questions.jsonl",
        responses_file: str = "pando_responses.jsonl"
    ):
        self.questions_file = questions_file
        self.responses_file = responses_file
        self.questions: Dict[str, Question] = {}
        self.responses: Dict[str, ProposalResponse] = {}
        self.load_state()
    
    def load_state(self):
        """Load questions and responses from files"""
        # Load questions
        try:
            with open(self.questions_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        q = Question(
                            id=data['id'],
                            timestamp=data['timestamp'],
                            task_id=data['task_id'],
                            category=data['category'],
                            question_text=data['question_text'],
                            context=data['context'],
                            blocking_level=BlockingLevel(data['blocking_level']),
                            assumed_answer=data.get('assumed_answer'),
                            deadline=data.get('deadline'),
                            status=QuestionStatus(data['status']),
                            options=data['options'],
                            user_response=data.get('user_response'),
                            user_response_timestamp=data.get('user_response_timestamp'),
                            branch_name=data.get('branch_name'),
                        )
                        self.questions[q.id] = q
        except FileNotFoundError:
            logger.info(f"No questions file found: {self.questions_file}")
        
        # Load responses
        try:
            with open(self.responses_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        r = ProposalResponse(
                            id=data['id'],
                            proposal_id=data['proposal_id'],
                            response_type=data['response_type'],
                            reason=data.get('reason'),
                            suggestions=data.get('suggestions', []),
                            timestamp=data.get('timestamp', datetime.now().isoformat()),
                        )
                        self.responses[r.id] = r
        except FileNotFoundError:
            logger.info(f"No responses file found: {self.responses_file}")

    def save_state(self):
        """Save questions and responses"""
        try:
            with open(self.questions_file, 'w') as f:
                for q in self.questions.values():
                    f.write(json.dumps(q.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to save questions: {e}")
        
        try:
            with open(self.responses_file, 'w') as f:
                for r in self.responses.values():
                    f.write(json.dumps(asdict(r)) + '\n')
        except Exception as e:
            logger.error(f"Failed to save responses: {e}")

    def pose_question(
        self,
        task_id: str,
        category: str,
        question_text: str,
        context: str,
        options: List[str],
        blocking_level: BlockingLevel = BlockingLevel.NON_BLOCKING,
        assumed_answer: Optional[str] = None,
        branch_name: Optional[str] = None,
        deadline_minutes: Optional[int] = None,
    ) -> Question:
        """
        Pose a question to the user.
        
        Args:
            task_id: Which task this question relates to
            category: Type of question
            question_text: The actual question
            context: Why this matters
            options: Possible responses
            blocking_level: Does this block work?
            assumed_answer: What will we do if user doesn't respond?
            branch_name: What branch we're working on for this
            deadline_minutes: When should user respond? (None = whenever)
        
        Returns:
            Question object
        """
        q_id = f"q_{uuid.uuid4().hex[:8]}"
        
        deadline = None
        if deadline_minutes:
            deadline = (
                datetime.now() + timedelta(minutes=deadline_minutes)
            ).isoformat()
        
        question = Question(
            id=q_id,
            timestamp=datetime.now().isoformat(),
            task_id=task_id,
            category=category,
            question_text=question_text,
            context=context,
            blocking_level=blocking_level,
            assumed_answer=assumed_answer,
            deadline=deadline,
            status=QuestionStatus.PENDING,
            options=options,
            branch_name=branch_name,
        )
        
        self.questions[q_id] = question
        self.save_state()
        logger.info(f"Question posed: {q_id} - {question_text[:50]}...")
        return question

    def record_response(self, question_id: str, response: str) -> bool:
        """
        Record user's response to a question.
        
        Returns:
            True if successful, False if question not found
        """
        question = self.questions.get(question_id)
        if not question:
            logger.error(f"Question not found: {question_id}")
            return False
        
        if response not in question.options and response != "custom":
            logger.warning(f"Response '{response}' not in options for {question_id}")
        
        question.mark_answered(response)
        self.save_state()
        logger.info(f"Response recorded for {question_id}: {response}")
        return True

    def get_pending_questions(self) -> List[Question]:
        """Get all questions waiting for user response"""
        return [
            q for q in self.questions.values()
            if q.status == QuestionStatus.PENDING
        ]

    def get_blocking_questions(self) -> List[Question]:
        """Get questions that are blocking current work"""
        return [
            q for q in self.questions.values()
            if q.status == QuestionStatus.PENDING
            and q.blocking_level == BlockingLevel.BLOCKING
        ]

    def get_overdue_questions(self) -> List[Question]:
        """Get questions past their deadline"""
        overdue = []
        for q in self.get_pending_questions():
            if q.deadline and datetime.fromisoformat(q.deadline) < datetime.now():
                overdue.append(q)
        return overdue

    def check_for_responses(self) -> List[Tuple[str, str]]:
        """
        Check if any pending questions have been answered.
        
        Returns:
            List of (question_id, response) tuples
        """
        new_responses = []
        for q in self.get_pending_questions():
            if q.user_response:
                new_responses.append((q.id, q.user_response))
        return new_responses

    def get_question_context(self, question_id: str) -> Dict:
        """
        Get full context about a question for the user dashboard.
        
        Returns:
            Dict with question details, status, and context
        """
        q = self.questions.get(question_id)
        if not q:
            return {}
        
        return {
            'id': q.id,
            'question': q.question_text,
            'context': q.context,
            'options': q.options,
            'assumed_answer': q.assumed_answer if q.blocking_level == BlockingLevel.NON_BLOCKING else None,
            'blocking': q.blocking_level == BlockingLevel.BLOCKING,
            'branch': q.branch_name,
            'time_asked_minutes_ago': (
                (datetime.now() - datetime.fromisoformat(q.timestamp)).total_seconds() / 60
            ),
            'deadline_minutes_remaining': (
                ((datetime.fromisoformat(q.deadline) - datetime.now()).total_seconds() / 60)
                if q.deadline else None
            ),
            'status': q.status.value,
            'user_response': q.user_response,
        }

    def record_proposal_response(
        self,
        proposal_id: str,
        response_type: str,  # "approve", "modify", "reject"
        reason: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ) -> bool:
        """
        Record user's response to a proposal (PR review).
        
        Args:
            proposal_id: ID of the proposal (usually PR ID)
            response_type: approve/modify/reject
            reason: Why user made this choice
            suggestions: Suggested modifications
        
        Returns:
            True if successful
        """
        r_id = f"r_{uuid.uuid4().hex[:8]}"
        response = ProposalResponse(
            id=r_id,
            proposal_id=proposal_id,
            response_type=response_type,
            reason=reason,
            suggestions=suggestions or [],
        )
        
        self.responses[r_id] = response
        self.save_state()
        logger.info(f"Proposal response recorded: {proposal_id} - {response_type}")
        return True

    def get_proposal_responses(self, proposal_id: str) -> List[ProposalResponse]:
        """Get all responses for a proposal"""
        return [r for r in self.responses.values() if r.proposal_id == proposal_id]

    def get_stats(self) -> Dict:
        """Get communication statistics"""
        pending = self.get_pending_questions()
        answered = [q for q in self.questions.values() if q.status == QuestionStatus.ANSWERED]
        resolved = [q for q in self.questions.values() if q.status == QuestionStatus.RESOLVED]
        
        return {
            'total_questions': len(self.questions),
            'pending': len(pending),
            'answered': len(answered),
            'resolved': len(resolved),
            'blocking_questions': len(self.get_blocking_questions()),
            'overdue_questions': len(self.get_overdue_questions()),
            'avg_response_time_minutes': (
                sum(
                    (datetime.fromisoformat(q.user_response_timestamp) -
                     datetime.fromisoformat(q.timestamp)).total_seconds() / 60
                    for q in answered
                ) / len(answered) if answered else 0
            ),
            'total_proposals': len(self.responses),
            'proposals_approved': len([r for r in self.responses.values() if r.response_type == 'approve']),
            'proposals_rejected': len([r for r in self.responses.values() if r.response_type == 'reject']),
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    comm = AsyncCommunicationSystem()
    
    # Pando poses a question
    q = comm.pose_question(
        task_id="t_001",
        category="technical_choice",
        question_text="Should we use Redis or in-memory caching?",
        context="JWT authentication needs caching for token validation",
        options=["Redis", "In-memory", "Hybrid"],
        blocking_level=BlockingLevel.NON_BLOCKING,
        assumed_answer="In-memory",
        branch_name="feature/jwt-auth-20260112",
    )
    print(f"Question posed: {q.id}")
    
    # User responds
    comm.record_response(q.id, "Redis")
    print(f"Response recorded for {q.id}")
    
    # Check for responses
    responses = comm.check_for_responses()
    print(f"New responses: {responses}")
    
    # Get context for dashboard
    ctx = comm.get_question_context(q.id)
    print(f"Question context: {ctx}")
