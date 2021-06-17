ids = dict()
for line in open('feature/fluidin.csv'):
    id=line.split(',')[1]
    ids[id] = ids.get(id, 0) + 1
print(ids)
