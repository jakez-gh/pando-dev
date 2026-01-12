"""
Pando Autonomous Decision Engine

Handles all decision-making for Pando's autonomous operations.
Implements confidence-based decision tree with multiple outcomes:
- EXECUTE: Run autonomously with high confidence
- PROPOSE: Create branch, propose to user
- BRANCH: Create exploratory branch with assumptions
- ASK: Ask user for blocking decision
- ESCALATE: Critical decision, needs immediate attention
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """Types of decisions Pando can make"""
    EXECUTE = "EXECUTE"  # Run autonomously, confidence > 0.85
    PROPOSE = "PROPOSE"  # Create branch, propose to user, confidence 0.65-0.85
    BRANCH = "BRANCH"    # Create assumption branch, continue work, confidence 0.45-0.65
    ASK = "ASK"          # Ask user for blocking decision, confidence < 0.45
    ESCALATE = "ESCALATE"  # Critical, immediate attention needed


class RiskLevel(Enum):
    """Risk assessment for decisions"""
    TRIVIAL = 0.1      # No risk to data/stability
    LOW = 0.5          # Minor impact if wrong
    MEDIUM = 0.7       # Moderate impact, needs testing
    HIGH = 0.85        # Significant impact, needs review
    CRITICAL = 0.95    # Data loss/security risk


@dataclass
class Decision:
    """Represents a decision made by Pando"""
    id: str
    timestamp: str
    task_id: str
    task_description: str
    decision_type: DecisionType
    confidence: float  # 0.0 - 1.0
    risk_level: RiskLevel
    reasoning: str
    selected_approach: Optional[str]
    alternatives_rejected: List[str]
    risks_identified: List[str]
    mitigation_strategies: List[str]
    assumed_values: Dict[str, str]  # For BRANCH decisions
    requires_blocking: bool  # True if task blocked until response
    outcome: Optional[str] = None  # Set after decision execution
    execution_time_seconds: Optional[float] = None
    success: Optional[bool] = None  # True/False/None


class AutonomyEngine:
    """
    Core decision-making engine for Pando.
    
    Evaluates tasks and decides autonomy level based on:
    - Task similarity to past tasks
    - Prerequisite availability
    - Model capability
    - Resource constraints
    - Risk assessment
    """

    def __init__(self, decision_history_file: str = "pando_decisions.json"):
        self.decision_history_file = decision_history_file
        self.decisions: List[Decision] = []
        self.load_decision_history()
        
        # Task similarity cache
        self.task_embeddings: Dict[str, str] = {}
        
        # Confidence calibration
        self.calibration = {
            "claimed_confidence": {},  # confidence_range -> [count, successes]
            "overall_quality": 0.0,
        }

    def load_decision_history(self):
        """Load previous decisions for learning"""
        try:
            with open(self.decision_history_file, 'r') as f:
                data = json.load(f)
                for d in data.get('decisions', []):
                    # Reconstruct decision objects
                    pass
        except FileNotFoundError:
            logger.info(f"No decision history file found: {self.decision_history_file}")
        except json.JSONDecodeError:
            logger.warning(f"Corrupted decision history: {self.decision_history_file}")

    def save_decision(self, decision: Decision):
        """Save decision to history"""
        self.decisions.append(decision)
        try:
            with open(self.decision_history_file, 'w') as f:
                json.dump({
                    'decisions': [asdict(d) for d in self.decisions],
                    'calibration': self.calibration,
                }, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save decision: {e}")

    def evaluate_task(
        self,
        task_id: str,
        task_description: str,
        prerequisites: Dict[str, bool],
        estimated_complexity: float,
        resource_available: Dict[str, float]
    ) -> Decision:
        """
        Main decision endpoint: evaluate a task and determine autonomy level.
        
        Args:
            task_id: Unique task identifier
            task_description: What needs to be done
            prerequisites: {"is_well_specified": True, "has_tests": True, ...}
            estimated_complexity: 0.0-1.0
            resource_available: {"gpu_memory": 6.5, "time_minutes": 120, ...}
        
        Returns:
            Decision object with reasoning and recommendation
        """
        
        # Step 1: Check if this is a known task type
        task_similarity = self._calculate_task_similarity(task_description)
        
        # Step 2: Check prerequisites
        prerequisites_ready = all(prerequisites.values())
        
        # Step 3: Assess model capability
        model_capability = self._assess_model_capability(
            task_description,
            estimated_complexity
        )
        
        # Step 4: Calculate confidence score
        base_confidence = (
            (task_similarity * 0.3) +
            (prerequisites_ready * 0.3) +
            (model_capability * 0.25) +
            (self._assess_resources(resource_available) * 0.15)
        )
        
        # Step 5: Apply risk multiplier
        risk_level = self._assess_risk(task_description)
        risk_multiplier = risk_level.value
        
        final_confidence = base_confidence * risk_multiplier
        final_confidence = max(0.0, min(1.0, final_confidence))  # Clamp 0-1
        
        # Step 6: Decision tree
        decision = self._decide_autonomy_level(
            task_id=task_id,
            task_description=task_description,
            confidence=final_confidence,
            risk_level=risk_level,
            prerequisites=prerequisites,
            task_similarity=task_similarity,
            model_capability=model_capability
        )
        
        self.save_decision(decision)
        return decision

    def _calculate_task_similarity(self, task_description: str) -> float:
        """
        Calculate how similar this task is to past tasks.
        Uses simple embedding-based similarity.
        
        Returns: 0.0-1.0, where 1.0 = exact match to previous task
        """
        # Create simple hash-based embedding
        description_hash = hashlib.md5(task_description.lower().encode()).hexdigest()
        
        if not self.decisions:
            return 0.0  # First task, no history
        
        # Look for similar past tasks
        max_similarity = 0.0
        for past_decision in self.decisions:
            if past_decision.success is True:  # Only learn from successes
                past_hash = hashlib.md5(
                    past_decision.task_description.lower().encode()
                ).hexdigest()
                
                # Simple similarity: count matching characters
                matches = sum(1 for a, b in zip(description_hash, past_hash) if a == b)
                similarity = matches / len(description_hash)
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity

    def _assess_model_capability(
        self,
        task_description: str,
        complexity: float
    ) -> float:
        """
        Assess if Llama 3.1 8B can handle this task.
        
        Returns: 0.0-1.0, where 1.0 = high confidence model can do it
        """
        # Keywords indicating high capability
        high_capability_keywords = [
            "python", "javascript", "refactor", "test", "document",
            "bug fix", "optimization", "analysis", "review"
        ]
        
        # Keywords indicating low capability
        low_capability_keywords = [
            "design system", "architecture redesign", "novel algorithm",
            "machine learning", "research"
        ]
        
        capability = 0.7  # Base capability
        
        # Adjust based on keywords
        for keyword in high_capability_keywords:
            if keyword in task_description.lower():
                capability += 0.05
        
        for keyword in low_capability_keywords:
            if keyword in task_description.lower():
                capability -= 0.1
        
        # Adjust based on complexity
        capability -= (complexity * 0.3)
        
        return max(0.0, min(1.0, capability))

    def _assess_resources(self, resource_available: Dict[str, float]) -> float:
        """
        Assess if resources are available for task execution.
        
        Returns: 0.0-1.0, where 1.0 = all resources available
        """
        # Check critical resources
        checks = []
        
        # GPU memory (6+ GB needed)
        gpu_mem = resource_available.get('gpu_memory_gb', 0)
        checks.append(min(1.0, gpu_mem / 6.0))
        
        # RAM (8+ GB needed)
        ram = resource_available.get('ram_gb', 0)
        checks.append(min(1.0, ram / 8.0))
        
        # Available time
        time_mins = resource_available.get('time_minutes', 0)
        checks.append(min(1.0, time_mins / 120.0))  # 2h baseline
        
        # Terminal availability
        terminals = resource_available.get('free_terminals', 0)
        checks.append(min(1.0, terminals / 4.0))
        
        return sum(checks) / len(checks) if checks else 0.5

    def _assess_risk(self, task_description: str) -> RiskLevel:
        """
        Assess risk level of task.
        
        Returns: RiskLevel enum
        """
        description_lower = task_description.lower()
        
        # Critical risks
        critical_keywords = [
            "delete", "production", "security", "password",
            "encryption", "database migration", "data loss",
            "merge to main", "deploy"
        ]
        
        if any(kw in description_lower for kw in critical_keywords):
            return RiskLevel.CRITICAL
        
        # High risk
        high_keywords = [
            "refactor architecture", "change api", "remove feature",
            "update dependency", "database schema"
        ]
        
        if any(kw in description_lower for kw in high_keywords):
            return RiskLevel.HIGH
        
        # Medium risk
        medium_keywords = [
            "performance", "optimization", "complex feature",
            "integration"
        ]
        
        if any(kw in description_lower for kw in medium_keywords):
            return RiskLevel.MEDIUM
        
        # Low risk
        low_keywords = [
            "documentation", "comment", "test", "lint",
            "small bug fix"
        ]
        
        if any(kw in description_lower for kw in low_keywords):
            return RiskLevel.LOW
        
        return RiskLevel.TRIVIAL

    def _decide_autonomy_level(
        self,
        task_id: str,
        task_description: str,
        confidence: float,
        risk_level: RiskLevel,
        prerequisites: Dict[str, bool],
        task_similarity: float,
        model_capability: float
    ) -> Decision:
        """
        Main decision tree: map confidence to decision type.
        
        confidence > 0.85 → EXECUTE
        0.65-0.85 → PROPOSE
        0.45-0.65 → BRANCH (with assumption)
        < 0.45 → ASK (blocking)
        """
        
        decision_id = f"d_{task_id}_{datetime.now().isoformat()}"
        now = datetime.now().isoformat()
        
        # Adjust decision based on risk
        if risk_level == RiskLevel.CRITICAL:
            # Always escalate critical
            return Decision(
                id=decision_id,
                timestamp=now,
                task_id=task_id,
                task_description=task_description,
                decision_type=DecisionType.ESCALATE,
                confidence=confidence,
                risk_level=risk_level,
                reasoning="Critical risk level - requires immediate user attention",
                selected_approach=None,
                alternatives_rejected=[],
                risks_identified=["Potential data loss or security impact"],
                mitigation_strategies=["User review and approval required"],
                assumed_values={},
                requires_blocking=True,
            )
        
        if confidence > 0.85:
            return Decision(
                id=decision_id,
                timestamp=now,
                task_id=task_id,
                task_description=task_description,
                decision_type=DecisionType.EXECUTE,
                confidence=confidence,
                risk_level=risk_level,
                reasoning=f"High confidence ({confidence:.1%}): Task similarity={task_similarity:.1%}, "
                          f"Model capability={model_capability:.1%}, Prerequisites ready",
                selected_approach="Execute autonomously",
                alternatives_rejected=["Ask user", "Create branch"],
                risks_identified=[],
                mitigation_strategies=["Standard testing", "Integration tests"],
                assumed_values={},
                requires_blocking=False,
            )
        
        elif confidence >= 0.65:
            return Decision(
                id=decision_id,
                timestamp=now,
                task_id=task_id,
                task_description=task_description,
                decision_type=DecisionType.PROPOSE,
                confidence=confidence,
                risk_level=risk_level,
                reasoning=f"Medium-high confidence ({confidence:.1%}): Good but not certain. "
                          f"Will create branch and propose approach to user.",
                selected_approach="Create feature branch, propose approach",
                alternatives_rejected=["Execute without review"],
                risks_identified=["Approach may not align with user expectations"],
                mitigation_strategies=["Branch allows easy pivoting", "User review before merge"],
                assumed_values={},
                requires_blocking=False,
            )
        
        elif confidence >= 0.45:
            # Identify key assumptions needed
            assumptions = self._identify_assumptions(task_description, prerequisites)
            
            return Decision(
                id=decision_id,
                timestamp=now,
                task_id=task_id,
                task_description=task_description,
                decision_type=DecisionType.BRANCH,
                confidence=confidence,
                risk_level=risk_level,
                reasoning=f"Medium confidence ({confidence:.1%}): Uncertain on some aspects. "
                          f"Will create assumption branch and continue work in parallel.",
                selected_approach="Branch with assumptions, parallel work",
                alternatives_rejected=["Execute", "Full blocking ask"],
                risks_identified=["Assumptions may need revision"],
                mitigation_strategies=["Isolated branch", "Easy to rebase when decision received"],
                assumed_values=assumptions,
                requires_blocking=False,
            )
        
        else:  # confidence < 0.45
            return Decision(
                id=decision_id,
                timestamp=now,
                task_id=task_id,
                task_description=task_description,
                decision_type=DecisionType.ASK,
                confidence=confidence,
                risk_level=risk_level,
                reasoning=f"Low confidence ({confidence:.1%}): Cannot proceed autonomously. "
                          f"Need user input to decide direction.",
                selected_approach="Ask user for guidance",
                alternatives_rejected=["Guess"],
                risks_identified=["Task blocked without clarification"],
                mitigation_strategies=["Waiting for user response", "Clear question asked"],
                assumed_values={},
                requires_blocking=True,
            )

    def _identify_assumptions(
        self,
        task_description: str,
        prerequisites: Dict[str, bool]
    ) -> Dict[str, str]:
        """
        Identify reasonable assumptions to proceed with.
        
        Examples:
        - "Use FastAPI" (could be Flask)
        - "100 requests/hour limit" (could be 1000)
        - "In-memory caching" (could be Redis)
        """
        
        assumptions = {}
        
        if "cache" in task_description.lower() and "type" not in prerequisites:
            assumptions["caching_type"] = "in-memory"
            assumptions["reasoning"] = "Starting with in-memory, can switch to Redis"
        
        if "api" in task_description.lower() and "framework" not in prerequisites:
            assumptions["framework"] = "FastAPI"
            assumptions["reasoning"] = "FastAPI is modern and performant, alternative: Flask"
        
        if "rate limit" in task_description.lower():
            assumptions["rate_limit"] = "100 requests/hour"
            assumptions["reasoning"] = "Conservative estimate, user can adjust"
        
        if "database" in task_description.lower() and "db_type" not in prerequisites:
            assumptions["database"] = "PostgreSQL"
            assumptions["reasoning"] = "Production-ready, alternative: SQLite for dev"
        
        return assumptions

    def record_outcome(
        self,
        decision_id: str,
        success: bool,
        execution_time_seconds: float,
        notes: str = ""
    ):
        """
        Record outcome of a decision for learning.
        
        Updates confidence calibration metrics.
        """
        for decision in self.decisions:
            if decision.id == decision_id:
                decision.success = success
                decision.execution_time_seconds = execution_time_seconds
                decision.outcome = notes
                
                # Update calibration
                confidence_range = self._get_confidence_range(decision.confidence)
                if confidence_range not in self.calibration["claimed_confidence"]:
                    self.calibration["claimed_confidence"][confidence_range] = [0, 0]
                
                count, successes = self.calibration["claimed_confidence"][confidence_range]
                if success:
                    successes += 1
                self.calibration["claimed_confidence"][confidence_range] = [count + 1, successes]
                
                self.save_decision(decision)
                break

    def _get_confidence_range(self, confidence: float) -> str:
        """Convert confidence score to range string"""
        if confidence > 0.9:
            return "> 90%"
        elif confidence > 0.8:
            return "80-90%"
        elif confidence > 0.7:
            return "70-80%"
        else:
            return "< 70%"

    def get_calibration_score(self) -> float:
        """
        Get calibration score: how well do confidence estimates match reality?
        
        Returns: 0.0-1.0, where 1.0 = perfect calibration
        """
        if not self.calibration["claimed_confidence"]:
            return 0.0
        
        accuracies = []
        for confidence_range, (count, successes) in self.calibration["claimed_confidence"].items():
            if count == 0:
                continue
            
            actual_rate = successes / count
            
            # Extract min confidence from range
            if "< 70" in confidence_range:
                expected_rate = 0.65
            elif "70-80" in confidence_range:
                expected_rate = 0.75
            elif "80-90" in confidence_range:
                expected_rate = 0.85
            else:  # > 90
                expected_rate = 0.95
            
            # How close is actual to expected?
            accuracy = 1.0 - abs(actual_rate - expected_rate)
            accuracies.append(accuracy)
        
        return sum(accuracies) / len(accuracies) if accuracies else 0.0


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    engine = AutonomyEngine()
    
    # Example: evaluate a task
    decision = engine.evaluate_task(
        task_id="t_001",
        task_description="Implement JWT authentication with refresh tokens",
        prerequisites={
            "is_well_specified": True,
            "has_tests": True,
            "framework_chosen": True,
        },
        estimated_complexity=0.65,
        resource_available={
            "gpu_memory_gb": 6.5,
            "ram_gb": 12,
            "time_minutes": 180,
            "free_terminals": 2,
        }
    )
    
    print(f"\nDECISION: {decision.decision_type.value}")
    print(f"Confidence: {decision.confidence:.1%}")
    print(f"Risk: {decision.risk_level.name}")
    print(f"Reasoning: {decision.reasoning}")
