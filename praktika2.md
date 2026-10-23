## 1

```bash
#!/bin/bash

python3 <<'PYTHON'
from importlib.metadata import distribution

package = distribution("matplotlib")
text = package.read_text("METADATA")
print(text)

for field in ["Name", "Version", "Summary", "Requires-Python", "Requires-Dist"]:
    print(field, package.metadata.get_all(field))
PYTHON

echo "Получить исходники из репозитория:"
echo "git clone https://github.com/matplotlib/matplotlib.git"
```

## 2

```bash
#!/bin/bash

curl -fL https://raw.githubusercontent.com/expressjs/express/master/package.json

echo "Получить исходники из репозитория:"
echo "git clone https://github.com/expressjs/express.git"
```

## 3

```bash
#!/bin/bash

python3 <<'PYTHON'
import json
import re
from urllib.request import urlopen
from importlib.metadata import distribution

package = distribution("matplotlib")

with open("matplotlib.dot", "w", encoding="utf-8") as file:
    file.write('digraph dependencies {\nrankdir=LR;\n')
    root = "matplotlib " + package.version
    for dependency in package.requires or []:
        name = re.match(r"[A-Za-z0-9_.-]+", dependency).group()
        file.write(json.dumps(root) + " -> " + json.dumps(name))
        file.write(" [label=" + json.dumps(dependency) + "];\n")
    file.write("}\n")

with urlopen("https://raw.githubusercontent.com/expressjs/express/master/package.json") as response:
    package = json.load(response)

with open("express.dot", "w", encoding="utf-8") as file:
    file.write('digraph dependencies {\nrankdir=LR;\n')
    root = "express " + package["version"]
    for name, version in package["dependencies"].items():
        file.write(json.dumps(root) + " -> " + json.dumps(name))
        file.write(" [label=" + json.dumps(version) + "];\n")
    file.write("}\n")
PYTHON

dot -Tsvg matplotlib.dot -o matplotlib.svg
dot -Tsvg express.dot -o express.svg
```

## 4

```bash
#!/bin/bash

cat > ticket.mzn <<'MODEL'
include "all_different.mzn";
array[1..6] of var 0..9: digit;
var 0..27: total = sum(i in 1..3)(digit[i]);
constraint all_different(digit);
constraint total = sum(i in 4..6)(digit[i]);
solve minimize total;
output ["ticket=" ++ concat([show(digit[i]) | i in 1..6]) ++
        "; sum=" ++ show(total) ++ "\n"];
MODEL

minizinc --solver gecode ticket.mzn
```

## 5

```bash
#!/bin/bash

cat > dependencies.mzn <<'MODEL'
int: P;
int: V;
int: D;
array[1..V] of 1..P: owner;
array[1..V] of string: label;
set of 1..V: required;
array[1..D] of 1..V: source;
array[1..D] of set of 1..V: allowed;
array[1..V] of var bool: selected;
constraint forall(p in 1..P)(
    sum(v in 1..V where owner[v] = p)(bool2int(selected[v])) <= 1
);
constraint forall(v in required)(selected[v]);
constraint forall(d in 1..D)(
    selected[source[d]] -> exists(v in allowed[d])(selected[v])
);
solve minimize sum(v in 1..V)(bool2int(selected[v]));
output [label[v] ++ "\n" | v in 1..V where fix(selected[v])];
MODEL

cat > task5.dzn <<'MODEL'
P=4; V=14; D=12;
owner=[1,2,2,2,2,2,2,3,3,3,3,3,4,4];
label=["root 1.0.0","menu 1.0.0","menu 1.1.0","menu 1.2.0","menu 1.3.0","menu 1.4.0","menu 1.5.0","dropdown 1.8.0","dropdown 2.0.0","dropdown 2.1.0","dropdown 2.2.0","dropdown 2.3.0","icons 1.0.0","icons 2.0.0"];
required={1};
source=[1,1,2,3,4,5,6,7,9,10,11,12];
allowed=[{2,3,4,5,6,7},{13},{8},{9,10,11,12},{9,10,11,12},{9,10,11,12},{9,10,11,12},{9,10,11,12},{14},{14},{14},{14}];
MODEL

minizinc --solver gecode dependencies.mzn task5.dzn
```

## 6

```bash
#!/bin/bash

cat > dependencies.mzn <<'MODEL'
int: P;
int: V;
int: D;
array[1..V] of 1..P: owner;
array[1..V] of string: label;
set of 1..V: required;
array[1..D] of 1..V: source;
array[1..D] of set of 1..V: allowed;
array[1..V] of var bool: selected;
constraint forall(p in 1..P)(
    sum(v in 1..V where owner[v] = p)(bool2int(selected[v])) <= 1
);
constraint forall(v in required)(selected[v]);
constraint forall(d in 1..D)(
    selected[source[d]] -> exists(v in allowed[d])(selected[v])
);
solve minimize sum(v in 1..V)(bool2int(selected[v]));
output [label[v] ++ "\n" | v in 1..V where fix(selected[v])];
MODEL

cat > task6.dzn <<'MODEL'
P=6; V=9; D=7;
owner=[1,2,2,3,4,5,5,6,6];
label=["root 1.0.0","foo 1.0.0","foo 1.1.0","left 1.0.0","right 1.0.0","shared 1.0.0","shared 2.0.0","target 1.0.0","target 2.0.0"];
required={1};
source=[1,1,3,3,4,5,6];
allowed=[{2,3},{9},{4},{5},{6,7},{6},{8}];
MODEL

minizinc --solver gecode dependencies.mzn task6.dzn
```

## 7

```bash
#!/bin/bash

cat > dependencies.mzn <<'MODEL'
int: P;
int: V;
int: D;
array[1..V] of 1..P: owner;
array[1..V] of string: label;
set of 1..V: required;
array[1..D] of 1..V: source;
array[1..D] of set of 1..V: allowed;
array[1..V] of var bool: selected;
constraint forall(p in 1..P)(
    sum(v in 1..V where owner[v] = p)(bool2int(selected[v])) <= 1
);
constraint forall(v in required)(selected[v]);
constraint forall(d in 1..D)(
    selected[source[d]] -> exists(v in allowed[d])(selected[v])
);
solve minimize sum(v in 1..V)(bool2int(selected[v]));
output [label[v] ++ "\n" | v in 1..V where fix(selected[v])];
MODEL
```
