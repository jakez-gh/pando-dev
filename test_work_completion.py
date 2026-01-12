#!/usr/bin/env python3
"""
Test work completion detection.

This script:
1. Creates a test task
2. Simulates agent completing it
3. Verifies coordinator.work_complete becomes True
"""

from task_engine import get_task_engine, TaskPriority
from agent_coordinator import get_coordinator
from message_bus import get_message_bus, Message
import time


def test_work_completion():
    print("=" * 60)
    print("WORK COMPLETION DETECTION TEST")
    print("=" * 60)
    
    # Initialize systems
    task_engine = get_task_engine()
    coordinator = get_coordinator()
    message_bus = get_message_bus()
    
    # Clear any existing state (for clean test)
    print("\n[1] Creating fresh instances...")
    
    # Create a test task
    print("\n[2] Creating test task...")
    task = task_engine.create_task(
        title="Test Implementation",
        description="Complete this test task",
        project_id="test-project",
        agent_role="implementer",
        priority=TaskPriority.HIGH.value
    )
    task_id = task.id
    print(f"  ✓ Task created: {task_id}")
    
    # Check initial state
    print("\n[3] Checking initial state...")
    print(f"  - Pending tasks: {len(task_engine.get_pending_tasks())}")
    print(f"  - Has work: {task_engine.has_work()}")
    print(f"  - Work complete: {coordinator.work_complete}")
    
    # Register agent
    print("\n[4] Registering agent...")
    agent_id = "test-agent-123"
    coordinator.register_agent(agent_id, "implementer")
    msg = Message(
        message_type="agent_ready",
        source_agent=agent_id,
        payload={"role": "implementer"}
    )
    message_bus.publish(msg)
    print(f"  ✓ Agent registered: {agent_id}")
    
    # Assign task to agent
    print("\n[5] Assigning task to agent...")
    coordinator.task_started(agent_id, task_id)
    print(f"  ✓ Task started")
    
    # Complete the task
    print("\n[6] Completing task...")
    time.sleep(0.5)  # Simulate work
    coordinator.task_complete(agent_id, task_id)
    msg = Message(
        message_type="task_complete",
        source_agent=agent_id,
        target_agent=task_id,
        payload={"task_id": task_id}
    )
    message_bus.publish(msg)
    print(f"  ✓ Task completed")
    
    # Check final state
    print("\n[7] Checking final state...")
    print(f"  - Pending tasks: {len(task_engine.get_pending_tasks())}")
    print(f"  - Has work: {task_engine.has_work()}")
    print(f"  - Work complete: {coordinator.work_complete}")
    print(f"  - Should continue: {coordinator.should_continue_running()}")
    
    # Verify the completion flag
    print("\n[8] TEST RESULT:")
    if coordinator.work_complete:
        print("  ✅ SUCCESS: work_complete flag is True")
        print("  ✅ System correctly detected all work is done")
        return True
    else:
        print("  ❌ FAILURE: work_complete flag is still False")
        return False


if __name__ == "__main__":
    try:
        success = test_work_completion()
        print("\n" + "=" * 60)
        if success:
            print("✅ WORK COMPLETION TEST PASSED")
        else:
            print("❌ WORK COMPLETION TEST FAILED")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
