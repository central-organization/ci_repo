log = "test test test...."

print(log)
with open("output/report.log",'w',encoding = 'utf-8') as f:
   f.write(log)