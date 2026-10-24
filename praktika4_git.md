## 1

```bash
git commit
git branch in
git checkout -b first
git commit
git commit
git checkout master
git commit
git commit
git merge first
git checkout in
git checkout -b second
git commit
git commit
git rebase master
git checkout master
git merge second
git checkout in
```

## 2

```bash
git --version
mkdir -p ~/Desktop/praktika4
cd ~/Desktop/praktika4
mkdir coder1
cd coder1
git init -b master
git config user.name "Леонид"
git config user.email "le0niddmitriev@yandex.ru"
echo 'print("Hello, Git!")' > prog.py
git status
git add prog.py
git commit -m "first commit"
git status
git log --oneline
```

## 3

```bash
git init --bare ../server
git remote add origin ../server
git remote -v
git push -u origin master

cd ..
git clone server coder2
cd coder2

git --git-dir=../server symbolic-ref HEAD refs/heads/master
git checkout -b master origin/master
ls
git status
git config user.name "Coder 2"
git config user.email "coder2@example.com"
printf '# Программа\n\nВыводит приветствие Hello, Git!\n\n## Авторы\n' > readme.md
git add readme.md
git commit -m "docs"
git push

cd ../coder1
git pull
echo 'Леонид — первый разработчик.' >> readme.md
git add readme.md
git commit -m "coder 1 info"
git push

cd ../coder2
echo 'Coder 2 — второй разработчик.' >> readme.md
git add readme.md
git commit -m "coder 2 info"
git push

git pull --no-rebase
cat readme.md

cat > readme.md <<'EOF'
# Программа

Выводит приветствие Hello, Git!

## Авторы
Леонид — первый разработчик.
Coder 2 — второй разработчик.
EOF
git add readme.md
git commit -m "readme fix"
git push
git status
git --no-pager log --graph --oneline

git --no-pager log --graph
```

## 4

```bash
git cat-file -p HEAD
git cat-file -p 'HEAD^{tree}'

cat > ../objects.py <<'EOF'
import subprocess

result = subprocess.run(
    ["git", "cat-file", "--batch-all-objects",
     "--batch-check=%(objectname) %(objecttype)"],
    capture_output=True,
    text=True,
    check=True
)

for line in result.stdout.splitlines():
    object_id, object_type = line.split()

    print("\nОбъект:", object_id, flush=True)
    print("Тип:", object_type, flush=True)

    subprocess.run(
        ["git", "cat-file", "-p", object_id],
        check=True
    )
EOF

cd ~/Desktop/praktika4/coder2
python3 ../objects.py
```
