# Repurposing a post

Do this after the post is final and has a live (or scheduled) URL. Same voice and humanizer rules as the post.

## LinkedIn post (≤1300 characters)

Readers see only the first two or three lines before "...see more", so line 1 carries the post.

- Line 1: the problem or the surprise, in one sentence. No "I'm excited to share".
- 3 to 6 short lines: what happened, the cause, the fix. One idea only.
- Optional: one small code snippet or command as plain text (LinkedIn doesn't format code).
- Last line: `Full write-up: https://alenabraham.me/posts/<slug>/`
- 2 or 3 hashtags at most, at the end. No emoji bullets.

Check the count before posting: `python3 -c 'import sys; print(len(sys.stdin.read()))' < linkedin.txt`

## X thread outline (5 to 8 posts)

1. The problem, stated so it stands alone. No "A thread".
2. The setup, in one or two lines.
3. What went wrong, with the exact error or symptom.
4. Why it happens. Attach the diagram PNG here if the post has one.
5. The fix: the one command or setting.
6. The trap or lesson that isn't obvious.
7. Link to the post.

Each post ≤280 characters. Write them as separate lines in the draft so they're easy to paste.
