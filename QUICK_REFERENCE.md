# Quick Reference - Performance & Security

## 🚀 FAISS Performance

### Search Speed
```
Before: ~500ms (100k faces)
After:  ~50ms  (100k faces)
Speedup: 10x faster
```

### Index Type
```
Old: IndexFlatIP (linear scan)
New: IndexIVFFlat (clustered)
```

### Rebuild Index
```bash
python migrate_faiss_index.py
```

---

## 🔒 Security Checklist

### Production Deployment
```bash
# 1. Set strong secret key
python -c "import secrets; print(secrets.token_hex(32))"

# 2. Update .env
FLASK_DEBUG=False
SECRET_KEY=<generated-key>

# 3. Change admin password
# Login and change via admin panel

# 4. Verify no credentials in logs
grep -r "password" logs/
```

### Environment Variables
```bash
# Required
SECRET_KEY=<strong-random-key>

# Optional
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
FLASK_DEBUG=False
```

---

## 🔧 Configuration

### FAISS Tuning
```python
# Adjust nlist based on dataset size
< 10k faces:    nlist=50
10k-100k:       nlist=100  (default)
100k-1M:        nlist=500
> 1M:           nlist=1000+
```

### Performance Testing
```python
from vector_search_service import get_face_search_service
import time

service = get_face_search_service()
start = time.time()
results = service.search(query_encoding, top_k=10)
print(f"Search time: {(time.time()-start)*1000:.2f}ms")
```

---

## 🐛 Troubleshooting

### Index Not Trained
```python
# Auto-trains on first insert
# Manual rebuild:
service.rebuild_from_database(PersonProfile.query.all())
```

### Env Variables Not Loading
```bash
# Check file exists
ls -la .env

# Verify python-dotenv
pip show python-dotenv

# Test loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('SECRET_KEY'))"
```

### Slow Search
```python
# Check index is trained
print(service.index.is_trained)

# Verify index size
print(service.get_index_size())

# Adjust nlist if needed
service = FaceVectorSearchService(nlist=500)
```

---

## 📊 Monitoring

### Performance Metrics
```python
# Index size
service.get_index_size()

# Search time
import time
start = time.time()
results = service.search(encoding)
elapsed = (time.time() - start) * 1000
print(f"{elapsed:.2f}ms")
```

### Security Audit
```bash
# Check for exposed credentials
grep -r "password\|secret\|key" *.py | grep -v ".env"

# Verify .env in .gitignore
cat .gitignore | grep .env

# Check debug mode
grep FLASK_DEBUG .env
```

---

## 📝 Quick Commands

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env
python run_app.py

# Migration
python migrate_faiss_index.py

# Generate secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Test environment
python -c "from config import Config; print('OK' if Config.SECRET_KEY else 'FAIL')"

# Check FAISS
python -c "from vector_search_service import get_face_search_service; s=get_face_search_service(); print(f'{s.get_index_size()} faces indexed')"
```

---

## 📚 Documentation

- [SECURITY_OPTIMIZATIONS.md](SECURITY_OPTIMIZATIONS.md) - Full documentation
- [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) - Change log
- [README.md](README.md) - Installation guide
- [.env.example](.env.example) - Configuration template

---

**Version:** 2.0 | **Status:** Production Ready ✅
