

class ToDo(db.Model):
  owner = db.User(auto_current_user_add=True)
  created = db.DateTimeProperty(auto_now_add=True)
  priority = db.IntegerProperty()
  description = db.TextProperty()
  due = db.DateProperty()
We create a new ToDo item and put it in the datastore.

PythonJava
my_todo = ToDo(priority=5, description='Fix that leaky faucet',
               due=datetime.date(2009, 8, 7))
my_todo.put()

# taken from: https://developers.google.com/appengine/articles/life_of_write

