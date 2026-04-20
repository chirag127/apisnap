import re

line = '@app.get("/users")'
method = "get"

# This is what the scanner code creates:
pattern = r"@(?:app|router)\." + method.lower() + r"(['\"])(.+?)\1"
print("Generated pattern:", repr(pattern))

match = re.match(pattern, line)
print("Match:", match)

if match:
    print("Groups:", match.groups())
