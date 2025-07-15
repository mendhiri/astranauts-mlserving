#!/usr/bin/env python3
"""
Script untuk menguji API endpoints Astranauts secara lokal
"""

import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:8080"  # Change this for different environments

def test_health_checks():
    """Test all health check endpoints"""
    print("🏥 Testing Health Checks...")
    
    endpoints = [
        "/health",
        "/api/v1/health", 
        "/api/v1/prabu/health",
        "/api/v1/sarana/health",
        "/api/v1/setia/health"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 200:
                print(f"✅ {endpoint}: OK")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Connection error - {e}")

def test_prabu_endpoints():
    """Test Prabu module endpoints"""
    print("\n💰 Testing Prabu Endpoints...")
    
    # Sample financial data
    sample_data = {
        "data_t": {
            "Jumlah aset": 1000000,
            "Jumlah liabilitas": 500000,
            "Jumlah ekuitas": 500000,
            "Pendapatan bersih": 800000,
            "Laba/rugi tahun berjalan": 100000,
            "Laba ditahan": 200000,
            "Jumlah aset lancar": 400000,
            "Jumlah liabilitas jangka pendek": 200000
        },
        "data_t_minus_1": {
            "Jumlah aset": 900000,
            "Jumlah liabilitas": 450000,
            "Jumlah ekuitas": 450000,
            "Pendapatan bersih": 750000,
            "Laba/rugi tahun berjalan": 90000
        },
        "is_public_company": False,
        "sector": "teknologi"
    }
    
    endpoints = [
        "/api/v1/prabu/calculate",
        "/api/v1/prabu/altman-z",
        "/api/v1/prabu/m-score",
        "/api/v1/prabu/metrics"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json=sample_data,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                print(f"✅ {endpoint}: OK")
            else:
                print(f"❌ {endpoint}: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")

def test_setia_endpoints():
    """Test Setia module endpoints"""
    print("\n📊 Testing Setia Endpoints...")
    
    sample_data = {
        "applicant_name": "PT Test Company",
        "industry_main": "Teknologi",
        "industry_sub": "Software",
        "use_gcs_for_risk_data": False
    }
    
    endpoints = [
        "/api/v1/setia/sentiment",
        "/api/v1/setia/news",
        "/api/v1/setia/external-risk"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json=sample_data,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                print(f"✅ {endpoint}: OK")
            else:
                print(f"❌ {endpoint}: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")

def test_api_documentation():
    """Test API documentation endpoints"""
    print("\n📚 Testing API Documentation...")
    
    endpoints = [
        "/docs",
        "/redoc",
        "/openapi.json"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 200:
                print(f"✅ {endpoint}: OK")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")

def main():
    print("🚀 Astranauts API Test Suite")
    print(f"Testing API at: {BASE_URL}")
    print("=" * 50)
    
    # Test all endpoints
    test_health_checks()
    test_prabu_endpoints()
    test_setia_endpoints()
    test_api_documentation()
    
    print("\n" + "=" * 50)
    print("🎉 API testing completed!")
    print(f"📚 API Documentation: {BASE_URL}/docs")

if __name__ == "__main__":
    main()
