"""
Real Race Condition Tests - No Mocks, Direct Function Calls
Tests both ATM-like critical section and file writing interference scenarios.
"""

import concurrent.futures
import random
from time import sleep
from click.testing import CliRunner
from main import submit

runner = CliRunner()

print("🏧 ATM RACE CONDITION")
print("💰 Initial balance: ₹1000")
print("🎫 10 customers, ₹200 each")

# Reset balance
init_cmd = "echo 1000 > /tmp/balance"
runner.invoke(submit, [init_cmd, "--wait", "--timeout=10"])

request_ids = [f"REQ{random.randint(1000, 9999)}" for _ in range(10)]
print(f"🎫 Requests: {', '.join(request_ids)}")

def submit_one(req_id):
    runner = CliRunner()
    cmd = f"""(
        flock 200
        echo '🔔 {req_id}: Customer arrived';
        BALANCE=$(cat /tmp/balance 2>/dev/null);
        echo '💰 {req_id}: Balance ₹'$BALANCE;
        if [ "$BALANCE" -ge 200 ] 2>/dev/null; then
            echo $((BALANCE - 200)) > /tmp/balance;
            echo '✅ {req_id}: SUCCESS';
        else
            echo '❌ {req_id}: FAILED';
        fi
        ) 200>/tmp/balance.lock
    """
    result = runner.invoke(submit, [cmd])
    return result

print("\n🚀 Submitting all 10 requests concurrently")
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(submit_one, rid) for rid in request_ids]

print(f"📨 10 requests submitted\n")
sleep(5)

# Wait for all futures and print job IDs
for future in concurrent.futures.as_completed(futures):
    result = future.result()
    # Extract Job ID line
    job_id_line = next((line for line in result.output.splitlines() if line.startswith("Job ID:")), None)
    if job_id_line:
        job_id = job_id_line.split("Job ID:")[1].strip()
        print(f"Job ID: {job_id}")
    else:
        print("⚠️ Job ID not found in output:")
        print(result.output)
