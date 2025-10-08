#!/bin/sh
current_branch=$(git rev-parse --abbrev-ref HEAD)

git checkout main
git pull origin main
git checkout "$current_branch"
git merge main
git checkout --theirs uv.lock
uv lock
git add uv.lock
git commit uv.lock -m "chore: upgrade dependencies"
git push origin "$current_branch"