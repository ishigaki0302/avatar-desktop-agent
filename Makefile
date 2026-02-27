.PHONY: dev build test lint install clean

install:
	pnpm install

dev: install
	pnpm dev

build: install
	pnpm build

test: install
	pnpm test

lint: install
	pnpm lint

clean:
	find . -name "dist" -type d -not -path "*/node_modules/*" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.tsbuildinfo" -not -path "*/node_modules/*" -delete 2>/dev/null || true
	find . -name "out" -type d -not -path "*/node_modules/*" -exec rm -rf {} + 2>/dev/null || true

reset: clean
	find . -name "node_modules" -type d -prune -exec rm -rf {} + 2>/dev/null || true
	pnpm install
