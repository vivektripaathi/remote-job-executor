import time
import random
import concurrent.futures
from click.testing import CliRunner
from main import submit

def test_file_writing_interference():
    """Test Case 2: File writing interference race condition"""
    runner = CliRunner()
    
    print("\n🖨️ SCENARIO: 6 people sending print jobs to shared printer simultaneously")
    print("📋 Expected: Print jobs should complete in order without mixing")
    print("🎯 Testing: Race condition in concurrent file writing operations\n")
    
    # Clear shared printer file before starting
    runner.invoke(submit, ["rm -f /tmp/shared_printer.txt", "--wait"])
    
    # Generate unique print job IDs
    job_ids = [f"JOB{random.randint(100, 999)}" for _ in range(6)]
    
    def send_print_job(job_id):
        """Simulate sending a print job with logging and file writing"""
        print_cmd = f"""
echo "📄 {job_id}: Print job submitted to shared printer";
echo "🖨️  {job_id}: Starting to print document...";
echo "=== PRINT JOB {job_id} START ===" >> /tmp/shared_printer.txt;
echo "📝 Document from {job_id} - Page 1" >> /tmp/shared_printer.txt;
echo "📝 Document from {job_id} - Page 2" >> /tmp/shared_printer.txt;
echo "📝 Document from {job_id} - Page 3" >> /tmp/shared_printer.txt;
echo "=== PRINT JOB {job_id} END ===" >> /tmp/shared_printer.txt;
echo "✅ {job_id}: Print job completed successfully";
LINES=$(wc -l < /tmp/shared_printer.txt);
echo "📊 {job_id}: Total lines in printer file: $LINES"
        """
        return runner.invoke(submit, [print_cmd.strip()])
    
    print("🚀 Sending 6 concurrent print jobs to remote shared printer...")
    
    # Fire all print jobs simultaneously
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(send_print_job, job_id) for job_id in job_ids]
        results = [future.result() for future in futures]
    
    # Collect job IDs
    print_job_ids = []
    accepted_jobs = 0
    for i, result in enumerate(results):
        if result.exit_code == 0:
            accepted_jobs += 1
            lines = result.output.strip().split('\n')
            for line in lines:
                if "Job ID:" in line:
                    job_id = line.split("Job ID: ")[1].strip()
                    print_job_ids.append((job_ids[i], job_id))
                    break
    
    print(f"\n📈 Print jobs fired: {len(job_ids)}")
    print(f"📨 Jobs accepted by system: {accepted_jobs}")
    
    # Wait for print jobs to complete
    print("\n⏳ Waiting for print jobs to complete...")
    time.sleep(5)
    
    # Check individual print job results using the view command
    print("\n📋 PRINT JOB RESULTS:")
    print("=" * 60)
    completed_jobs = 0
    
    for job_id_name, job_id in print_job_ids:
        print(f"🔍 Checking {job_id_name} (Job: {job_id[:8]}...):")
        view_result = runner.invoke(submit, ["view", job_id])
        
        if view_result.exit_code == 0:
            if "Print job completed successfully" in str(view_result.output):
                print(f"   ✅ {job_id_name}: Print job completed successfully")
                completed_jobs += 1
            else:
                print(f"   ❌ {job_id_name}: Print job failed or incomplete")
            
            # Show key parts of the job output
            lines = view_result.output.split('\n')
            for line in lines:
                if f"{job_id_name}:" in line and ("completed" in line or "submitted" in line):
                    print(f"   📝 {line.strip()}")
        else:
            print(f"   ⚠️  Could not view job {job_id_name}")
    
    # Show final printer output and check for interference
    print("\n📄 Final printer file contents:")
    content_result = runner.invoke(submit, ["cat /tmp/shared_printer.txt", "--wait"])
    printer_content = content_result.output.strip()
    
    if printer_content:
        lines = [line for line in printer_content.split('\n') if line.strip()]
        for i, line in enumerate(lines[-15:], 1):  # Show last 15 lines
            print(f"   {i:2d}: {line.strip()}")
        
        # Check for interference (interleaved job segments)
        interference_detected = False
        current_job = None
        
        for line in lines:
            if "START" in line and "JOB" in line:
                current_job = line.split("JOB")[1].split()[0]
            elif "END" in line and "JOB" in line:
                end_job = line.split("JOB")[1].split()[0]
                if current_job != end_job:
                    interference_detected = True
                    break
        
        print("=" * 60)
        print(f"📊 PRINT JOB SUMMARY:")
        print(f"   📄 Jobs completed successfully: {completed_jobs}")
        print(f"   🖨️  Interference detected: {'YES' if interference_detected else 'NO'}")
        print(f"   🎯 File writing test: {'INTERFERENCE FOUND' if interference_detected else 'CLEAN OUTPUT'}")
    else:
        print("❌ No printer output found")

if __name__ == "__main__":
    print("🔬 === REAL RACE CONDITION TESTING SUITE ===")
    print("🎯 Testing concurrent command execution on remote system")
    print("⚡ No mocks - Real commands, Real race conditions\n")
    
    # Run the tests
    test_file_writing_interference()
    
    print("\n🏁 === RACE CONDITION TESTS COMPLETE ===")
    print("📊 Check the streamed output above for detailed results")
