.PHONY: test clean cache run commit

test:
	python3 src/tests/test_agent_behavior.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

cache:
	rm -rf .anthropic_cache 2>/dev/null || true
	@echo "Cache cleared"

run:
	python send.py

commit:
	git add .
	git status
	@echo "Ready to commit. Run: git commit -m 'your message'"