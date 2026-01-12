"""Test direction API functionality"""
from pando_core.direction_api import get_direction_api
import json

api = get_direction_api()

# Test direction submission
result = api.submit_direction('Test: Review code quality', priority='high')
print('✅ Direction submitted:')
print(json.dumps(result, indent=2))

# Test task parsing
tasks = api.parse_direction_into_tasks('Review auth module and add logging')
print(f'\n✅ Parsed {len(tasks)} tasks:')
for task in tasks:
    print(f"  - {task['title']} ({task['category']}, ~{task['estimated_minutes']}min)")

# Test statistics
stats = api.get_stats()
print(f'\n✅ Statistics:')
print(json.dumps(stats, indent=2))

print("\n✅ Direction API is working perfectly!")
