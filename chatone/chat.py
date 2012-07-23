import datetime

app_ver = '1.3'
app_name = 'Chat.py w proper refresh'

print 'Content-Type: text/html'
print ''
print '<html><head>'
print ' <title>Welcome to Riccardo %s service</title>' % app_name
print ' <META HTTP-EQUIV="refresh" CONTENT="2; URL=/">'
print '</head><body>'
print '<h1>Riccardo %s service v%s</h1>' % (app_name,app_ver)

print '<p>Current time is: %s</p>' % (datetime.datetime.now())
print '<p>App name:    <b>%s</b></p>' % (app_name)
print '<p>App version: <b>%s</b></p>' % (app_ver)

print '</body></html>'
