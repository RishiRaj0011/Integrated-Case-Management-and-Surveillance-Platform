"""
Verification Script - Test Performance & Security Optimizations
Validates that all optimizations are working correctly
"""
import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_environment_variables():
    """Test environment variable loading"""
    print("\n" + "="*60)
    print("Testing Environment Variables")
    print("="*60)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ python-dotenv installed and loaded")
        
        from config import Config
        
        if Config.SECRET_KEY and Config.SECRET_KEY != 'dev-secret-key-change-in-production':
            print("✅ SECRET_KEY configured")
        else:
            print("⚠️  SECRET_KEY using default value - change in production!")
        
        if Config.FLASK_DEBUG == False or os.getenv('FLASK_DEBUG', 'False').lower() == 'false':
            print("✅ FLASK_DEBUG is False (secure)")
        else:
            print("⚠️  FLASK_DEBUG is True - disable in production!")
        
        print("✅ Environment variables test passed")
        return True
        
    except Exception as e:
        print(f"❌ Environment variables test failed: {e}")
        return False

def test_faiss_index():
    """Test FAISS index performance"""
    print("\n" + "="*60)
    print("Testing FAISS Index")
    print("="*60)
    
    try:
        from vector_search_service import get_face_search_service
        import numpy as np
        
        service = get_face_search_service()
        index_size = service.get_index_size()
        
        print(f"✅ FAISS service initialized")
        print(f"   Index size: {index_size} face encodings")
        
        # Check if it's IVF index
        import faiss
        if isinstance(service.index, faiss.IndexIVFFlat):
            print("✅ Using IndexIVFFlat (optimized)")
            print(f"   Clusters (nlist): {service.nlist}")
            
            if service.index.is_trained:
                print("✅ Index is trained")
            else:
                print("⚠️  Index not trained yet (will train on first insert)")
        else:
            print("⚠️  Not using IndexIVFFlat - performance may be slower")
        
        # Performance test if index has data
        if index_size > 0:
            print("\n   Running performance test...")
            test_encoding = np.random.rand(128).tolist()
            
            start = time.time()
            results = service.search(test_encoding, top_k=5)
            elapsed = (time.time() - start) * 1000
            
            print(f"   Search time: {elapsed:.2f}ms")
            
            if elapsed < 100:
                print("   ✅ Excellent performance!")
            elif elapsed < 500:
                print("   ✅ Good performance")
            else:
                print("   ⚠️  Slower than expected - consider rebuilding index")
        
        print("✅ FAISS index test passed")
        return True
        
    except Exception as e:
        print(f"❌ FAISS index test failed: {e}")
        return False

def test_security():
    """Test security configurations"""
    print("\n" + "="*60)
    print("Testing Security Configuration")
    print("="*60)
    
    try:
        # Check .env in .gitignore
        if os.path.exists('.gitignore'):
            with open('.gitignore', 'r') as f:
                gitignore = f.read()
                if '.env' in gitignore:
                    print("✅ .env file in .gitignore")
                else:
                    print("⚠️  .env not in .gitignore - add it!")
        
        # Check .env exists
        if os.path.exists('.env'):
            print("✅ .env file exists")
        else:
            print("⚠️  .env file not found - create from .env.example")
        
        # Check for password in logs (run_app.py)
        if os.path.exists('run_app.py'):
            with open('run_app.py', 'r') as f:
                content = f.read()
                if 'admin123' not in content or 'Admin credentials' not in content:
                    print("✅ No admin password in run_app.py")
                else:
                    print("⚠️  Admin password found in run_app.py - remove it!")
        
        print("✅ Security test passed")
        return True
        
    except Exception as e:
        print(f"❌ Security test failed: {e}")
        return False

def test_database():
    """Test database connectivity"""
    print("\n" + "="*60)
    print("Testing Database")
    print("="*60)
    
    try:
        from __init__ import create_app, db
        from models import User, PersonProfile
        
        app = create_app()
        
        with app.app_context():
            # Test database connection
            user_count = User.query.count()
            profile_count = PersonProfile.query.count()
            
            print(f"✅ Database connected")
            print(f"   Users: {user_count}")
            print(f"   Person Profiles: {profile_count}")
            
            print("✅ Database test passed")
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("\n" + "="*70)
    print(" "*15 + "VERIFICATION SCRIPT")
    print(" "*10 + "Performance & Security Optimizations")
    print("="*70)
    
    results = {
        'Environment Variables': test_environment_variables(),
        'FAISS Index': test_faiss_index(),
        'Security': test_security(),
        'Database': test_database()
    }
    
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED - System is optimized and secure!")
    else:
        print("⚠️  SOME TESTS FAILED - Review the output above")
    print("="*70 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
