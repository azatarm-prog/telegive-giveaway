#!/usr/bin/env python3
"""
Local test script to debug Auth Service integration
"""

import requests
import json
import os
import sys

def test_auth_service_direct():
    """Test Auth Service directly"""
    print("🔍 Testing Auth Service directly...")
    
    auth_url = "https://web-production-ddd7e.up.railway.app"
    test_account_id = 262662172
    
    url = f"{auth_url}/api/v1/bots/validate/{test_account_id}"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ Direct Auth Service Test:")
        print(f"   URL: {url}")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.ok:
            data = response.json()
            print(f"   Valid: {data.get('valid', False)}")
            return True
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_giveaway_service_health():
    """Test Giveaway Service health"""
    print("\n🏥 Testing Giveaway Service health...")
    
    giveaway_url = "https://telegive-giveaway-production.up.railway.app"
    
    try:
        response = requests.get(f"{giveaway_url}/health", timeout=10)
        print(f"✅ Giveaway Service Health:")
        print(f"   Status: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print(f"   Service Status: {data.get('status')}")
            print(f"   Auth Service: {data.get('external_services', {}).get('auth_service')}")
            return True
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_giveaway_creation():
    """Test giveaway creation"""
    print("\n🎯 Testing Giveaway Creation...")
    
    giveaway_url = "https://telegive-giveaway-production.up.railway.app"
    test_data = {
        "account_id": 262662172,
        "title": "Debug Test Giveaway",
        "main_body": "This is a debug test to identify the Auth Service integration issue"
    }
    
    try:
        response = requests.post(
            f"{giveaway_url}/api/giveaways/create",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"✅ Giveaway Creation Test:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.ok:
            data = response.json()
            print(f"   Success: {data.get('success', False)}")
            return True
        else:
            try:
                error_data = response.json()
                print(f"   Error Code: {error_data.get('error_code')}")
                print(f"   Error Message: {error_data.get('error')}")
            except:
                print(f"   Raw Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_environment_variables():
    """Check environment variables that might affect the integration"""
    print("\n🔧 Environment Variables Check:")
    
    # Test what the service thinks its Auth URL is
    giveaway_url = "https://telegive-giveaway-production.up.railway.app"
    
    # Try to access debug endpoint if it exists
    try:
        response = requests.get(f"{giveaway_url}/debug/auth-config", timeout=10)
        if response.ok:
            data = response.json()
            print(f"   Auth Service URL: {data.get('auth_service_url')}")
        else:
            print(f"   Debug endpoint not available (status: {response.status_code})")
    except:
        print(f"   Debug endpoint not accessible")

def main():
    """Main test function"""
    print("🚀 Auth Service Integration Debug Test")
    print("=" * 50)
    
    # Test 1: Direct Auth Service
    auth_works = test_auth_service_direct()
    
    # Test 2: Giveaway Service Health
    health_works = test_giveaway_service_health()
    
    # Test 3: Environment Variables
    check_environment_variables()
    
    # Test 4: Giveaway Creation
    creation_works = test_giveaway_creation()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Auth Service Direct: {'✅ PASS' if auth_works else '❌ FAIL'}")
    print(f"   Giveaway Health: {'✅ PASS' if health_works else '❌ FAIL'}")
    print(f"   Giveaway Creation: {'✅ PASS' if creation_works else '❌ FAIL'}")
    
    if auth_works and health_works and not creation_works:
        print("\n🔍 Analysis:")
        print("   - Auth Service is working correctly")
        print("   - Giveaway Service is healthy")
        print("   - Issue is in the integration between services")
        print("   - Likely causes:")
        print("     1. Environment variable TELEGIVE_AUTH_URL not set correctly")
        print("     2. Code changes not deployed yet")
        print("     3. Internal server error in validation logic")
        
        print("\n🛠️  Recommended Actions:")
        print("   1. Check Railway environment variables")
        print("   2. Verify latest code is deployed")
        print("   3. Check Railway deployment logs")
        print("   4. Add more detailed logging")

if __name__ == "__main__":
    main()

