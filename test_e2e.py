#!/usr/bin/env python3
"""
End-to-end test script for Excel Runner.
Tests: upload, run, status polling, logs, results, download.
Requires: backend running on http://localhost:8080
"""
import json
import sys
import time
from pathlib import Path
import requests
from io import BytesIO

BASE_URL = "http://localhost:8080"
TIMEOUT = 60  # seconds to wait for job completion

def test_e2e():
    print("[1] Creating dummy .xlsx files for upload...")
    # Create minimal Excel-like files (we'll just use .xlsx extension for this test)
    test_files = []
    for i in range(2):
        fname = f"test_input_{i}.xlsx"
        Path(fname).write_bytes(b"PK\x03\x04" + b"dummy" * 100)  # Fake ZIP header + data
        test_files.append(fname)
    
    print(f"[2] Uploading {len(test_files)} files...")
    with open(test_files[0], 'rb') as f1, open(test_files[1], 'rb') as f2:
        files = [('files', f1), ('files', f2)]
        resp = requests.post(f"{BASE_URL}/upload", files=files)
    
    if resp.status_code != 200:
        print(f"ERROR: Upload failed with {resp.status_code}: {resp.text}")
        return False
    
    data = resp.json()
    session_id = data.get('session_id')
    print(f"✓ Upload successful. session_id: {session_id}")
    
    print("[3] Running job...")
    resp = requests.post(f"{BASE_URL}/run", json={
        "session_id": session_id,
        "options": {"check_schema": False, "locale": "it"}
    })
    
    if resp.status_code != 200:
        print(f"ERROR: Run failed with {resp.status_code}: {resp.text}")
        return False
    
    job_id = resp.json().get('job_id')
    print(f"✓ Job started. job_id: {job_id}")
    
    print("[4] Polling status...")
    start = time.time()
    while time.time() - start < TIMEOUT:
        resp = requests.get(f"{BASE_URL}/status/{job_id}")
        if resp.status_code != 200:
            print(f"ERROR: Status check failed: {resp.text}")
            return False
        
        status_data = resp.json()
        status = status_data.get('status')
        progress = status_data.get('progress', 0)
        message = status_data.get('message', '')
        print(f"  Status: {status} | Progress: {progress}% | Message: {message}")
        
        if status in ('succeeded', 'failed'):
            break
        time.sleep(1)
    
    if status != 'succeeded':
        print(f"ERROR: Job ended with status '{status}'")
        return False
    
    print("✓ Job succeeded")
    
    print("[5] Fetching logs...")
    resp = requests.get(f"{BASE_URL}/logs/{job_id}")
    if resp.status_code == 200:
        log_text = resp.text
        print(f"✓ Logs retrieved ({len(log_text)} bytes):")
        print("---")
        print(log_text[:500])
        print("---")
    
    print("[6] Fetching results...")
    resp = requests.get(f"{BASE_URL}/results/{job_id}")
    if resp.status_code != 200:
        print(f"ERROR: Results fetch failed: {resp.text}")
        return False
    
    results = resp.json()
    print(f"✓ Results: {len(results)} files")
    for r in results:
        print(f"  - {r['filename']} ({r['size_bytes']} bytes)")
    
    if len(results) == 0:
        print("WARNING: No output files generated")
    
    print("[7] Downloading first result...")
    if results:
        first_file = results[0]['filename']
        resp = requests.get(f"{BASE_URL}/download/{job_id}/{first_file}")
        if resp.status_code == 200:
            print(f"✓ Downloaded {first_file} ({len(resp.content)} bytes)")
        else:
            print(f"ERROR: Download failed: {resp.status_code}")
            return False
    
    print("[8] Downloading all results as ZIP...")
    resp = requests.get(f"{BASE_URL}/download/{job_id}/all.zip")
    if resp.status_code == 200:
        print(f"✓ Downloaded all.zip ({len(resp.content)} bytes)")
    else:
        print(f"ERROR: ZIP download failed: {resp.status_code}")
        return False
    
    print("[9] Cleanup...")
    for fname in test_files:
        Path(fname).unlink(missing_ok=True)
    
    print("\n✓✓✓ E2E test PASSED ✓✓✓")
    return True

if __name__ == "__main__":
    try:
        success = test_e2e()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
