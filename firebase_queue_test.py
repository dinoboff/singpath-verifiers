import json
import random
import time
import sys
import urllib.request
import urllib.parse
from urllib.request import urlopen

thedifference = 0
verifier_name = "Verifier"
create_problems = False
num_users = 5
options = """Available options
create_problems=true
verifier_name=Verifier_X
"""
print(options)

if len(sys.argv)>1:
    for i in range(1,len(sys.argv)):
        entry = sys.argv[i].split("=")
        if entry[0] == 'name':
            verifier_name = entry[1]
        elif entry[0] == 'create_problems':
            create_problems = True
        elif entry[0] == 'users':
            num_users = int(entry[1])

print("Testing verify queue on Firebase as "+verifier_name)

token1 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE0NDYwODQyODUsImQiOnsiaXNfdmVyaWZpZXIiOnRydWUsIm90aGVyX2F1dGhfZGF0YSI6ImJhciIsInVpZCI6InZlcmlmaWVyXzEifSwidiI6MH0.0Z13TBFjARLcuachbqrf45qrAdNi7vOTGQKNd4JyBto"
token2 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ2IjowLCJkIjp7InVpZCI6InZlcmlmaWVyXzIiLCJpc192ZXJpZmllciI6dHJ1ZSwib3RoZXJfYXV0aF9kYXRhIjoiYmFyIn0sImlhdCI6MTQ0NjA4NDQyMn0.2wbTONeLpDuORUJhYI1cOC3Eh_gnxDPdiayGc2KjPc0"

firebaseToken = token1

firebase_url = 'https://verifier.firebaseio.com'
taskqueue_url = firebase_url + '/taskqueue'
tasklog_url = firebase_url + '/tasklog'

test_users = []
for x in range(num_users):
    test_users.append("TEST_USER_"+str(x))	

def get_new_token(uid):
    from firebase_token_generator import create_token
    auth_payload = { "uid": uid, "is_verifier": True, "other_auth_data": "bar" }
    FIREBASE_SECRET ="YOUR TOKEN GOES HERE"
    token = create_token(FIREBASE_SECRET, auth_payload)
    return token

# POST add new key
# curl -X POST -d '{"user_id" : "jack", "text" : "Ahoy!"}'   'https://verifier.firebaseio.com/taskqueue.json'
# PUT update existing key
# curl -X PUT -d '{ "first": "Jack", "last": "Sparrow" }'   'https://verifier.firebaseio.com/taskqueue/-K1lU0_DWs10SaXxqgxa.json'
# DELETE existing key
# curl -X DELETE   'https://verifier.firebaseio.com/taskqueue/-K1lU0_DWs10SaXxqgxa.json'

import sys
if sys.version_info.major == 3:
  from urllib.request import HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, Request, build_opener
  from urllib.parse import urlencode
else:
  from urllib2 import HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, Request, build_opener
  from urllib import urlencode

# This is a python 3 way to execute curl commands. 
def curl(url, params=None, auth=None, req_type="GET", data=None, headers=None):
  post_req = ["POST", "PUT"]
  get_req = ["GET", "DELETE"]

  if params is not None:
    url += "?" + urlencode(params)

  if req_type not in post_req + get_req:
    raise IOError("Wrong request type \"%s\" passed" % req_type)

  _headers = {}
  handler_chain = []

  if auth is not None:
    manager = HTTPPasswordMgrWithDefaultRealm()
    manager.add_password(None, url, auth["user"], auth["pass"])
    handler_chain.append(HTTPBasicAuthHandler(manager))

  if req_type in post_req and data is not None:
    _headers["Content-Length"] = len(data)

  if headers is not None:
    _headers.update(headers)

  director = build_opener(*handler_chain)

  if req_type in post_req:
    if sys.version_info.major == 3:
      _data = bytes(data, encoding='utf8')
    else:
      _data = bytes(data)

    req = Request(url, headers=_headers, data=_data)
  else:
    req = Request(url, headers=_headers)

  req.get_method = lambda: req_type
  result = director.open(req)

  return {
    "httpcode": result.code,
    "headers": result.info(),
    "content": result.read()
  }


def firebase_get(url, data=""):
	result = curl(url+".json", req_type="GET", data=json.dumps(data))
	raw = result['content'].decode()
	data = json.loads(raw)
	return data
	
def firebase_post(url,data):
	result = curl(url+".json", req_type="POST", data=json.dumps(data))
	raw = result['content'].decode()
	result = json.loads(raw)
	return result

def firebase_put(url,data):
	result = curl(url+".json", req_type="PUT", data=json.dumps(data))
	raw = result['content'].decode()
	result = json.loads(raw)
	return result

def firebase_delete(url):
    #print(url+".json")
    result = curl(url+".json", req_type="DELETE")
    raw = result['content']
    #result = json.loads(raw)
    return raw

def log_task_completion(task):
    # Once the task has been deleted, add a record to the tasklog.
    task["verified"] = get_firebase_time()
    task["duration"] = task["verified"] - task["created"]
    firebase_post(tasklog_url, task)
    return True
    
def delete_task(key, task):
    # Have to be careful to only delete problems of the original timestamp. 
    # The users may resubmit before verification complete. 
    # Should not delete the new request. So we have to check timestamp before deleting. 
    # print("Deleting task {}.".format(key))
    url = taskqueue_url + "/" + key
    data = None
    
    # Check timestamp and then delete. 
    # Still a concurrency bug if users submits again between this fetch and delete. 
    # lock or transaction if we could
    latest_task = firebase_get(url)
    if "created" in latest_task and latest_task["created"] == task["created"]:
      try:
        data = firebase_delete(url)       
      except:
        print("Could not delete problem")
        
      log_task_completion(latest_task)
    else:
        print("Solution was updated before delete completed.")    
    
    return data	

# Create a task from a random user. 
def create_task():
    user = random.choice(test_users)
    url = taskqueue_url+"/"+user
    print("Adding task for user {}".format(user))
    data = {"user": user,
           "problem":"456", 
           "created":{".sv": "timestamp"},
		   "version":1}
    result = None
    # Todo: if the problem already exists, this will cause an error. 
    # Allow users to overwrite problems by making version == 1 
    
    try: 
        result = firebase_put(url=url, data=data)
    except:
        print("*** Error creating task.  ***")
    
    return result

# Fetch all tasks
def fetch_tasks(count=100):
	data = firebase_get(taskqueue_url)
	return data

def reserve_task(key, task, seconds=30):
    data = None    
    # Get current task
    #print("reserving task")
    url = taskqueue_url + "/" + key
    #task = firebase_get(url)
    """
    By the time you are getting here after your additional tasks fetch, 
    The other verifier has reserved. You should just post to immediately reserve in the loop. 
    
    This below should be an immediate PUT. 
    """
    
    # Update task and write back. 
    if task:
        task['reserved_at'] = {".sv": "timestamp"}
        #print("Current version {} writing new version {}".format(task['version'] , task['version'] +1))
        task['version'] = task['version']+1
        task['reserved_by'] = verifier_name
        #print("put task")
        try:
            #updating task 
            data = firebase_put(url=url, data=task)
        except:
            #Update failed. 
            pass
            #print("Reservation update failed.")
    return data	


# Assuming python time is epoch time. 
def get_firebase_time(updatetime = False):
    epoch_time = int(time.time()*1000)
    thedifference = 0
    if updatetime: 
        print("Python epoch time    {}".format(epoch_time))
        data = {".sv": "timestamp"}
        url = firebase_url + "/server_time" 
        result = firebase_put(url=url, data=data)
        thedifference = epoch_time - result
        print("Difference between   {}".format(thedifference))
        print("Python adjusted {}".format(epoch_time + thedifference))
        print("Fireabase epoch time {}".format(result))
        
    return epoch_time + thedifference 

def get_next_available_task():
    max_time = 30000 # Find tasks older than 30s then unreserved. 
    tasks = fetch_tasks()
    current_server_time = get_firebase_time()
    maximum_age ={"key":None, "age":0}
    oldest_unreserved = {"key":None, "age":0}
    #print("There are {} tasks to process.".format(len(tasks)))
    if tasks ==None: 
        tasks = {}
    for task_key in tasks:
        age = 0
        is_reserved = "reserved_at" in tasks[task_key].keys()
        if is_reserved: 
            age = current_server_time - tasks[task_key]['reserved_at']
            if maximum_age['key']==None or maximum_age['age'] < age:
                maximum_age =  {"key":task_key, "age":age}
        else:
            age = current_server_time - tasks[task_key]['created']
            if oldest_unreserved['key']==None or oldest_unreserved['age'] < age:
                oldest_unreserved =  {"key":task_key, "age":age}

    if maximum_age['key'] !=None and maximum_age['age']>max_time:
        #print("Returning the oldest reserved task is {} at {}".format(maximum_age['key'], maximum_age['age']))
        return maximum_age['key'], tasks[maximum_age['key']]
    elif oldest_unreserved['key'] !=None:
        #print("Returning the oldest unreserved task is {} at {}".format(oldest_unreserved['key'], oldest_unreserved['age']))
        return oldest_unreserved['key'], tasks[oldest_unreserved['key']]
    else: 
        return None, None

def find_and_reserve_next_task():
    # Have to return the task and key to keep track of timestamp. 
    task_key, task = get_next_available_task()
    if task_key == None:
      return None, None
    else:
        task = reserve_task(task_key, task, seconds=30)
        if task: 
            #print("Verifier reserved task {}".format(task_key))
            #print(task)
            pass
        else:
            # This may not be a reason to pass a None which will look like a miss and cause sleep. 
            #print("*** Another verifier reserved {} before I could.***".format(task_key))
            # Try recursive calling
            return find_and_reserve_next_task()
            #task_key = None
        return task_key, task
        

#reserved_task_key, reserved_task = find_and_reserve_next_task()    
#print("The next reserved task to process is key {}".format(reserved_task_key, reserved_task))

# Todo: Leaving this with a concurrency error. 
# Need a validation rule that will check the version number before allowing reservation updates. 
# Then need to remove the checking of server time. Just need to compare to local clock once. 

def keep_solving_problems():
    no_task_found = []
    while True:
        reserved_task_key, task = find_and_reserve_next_task()  
        #print("In keep solving key back in {}".format(reserved_task_key))
        # This could be from a error or no task to verify  
        if reserved_task_key==None:
            if len(no_task_found)<60:
                no_task_found.append(1)
            sleep_time = len(no_task_found)
            print("Sleeping for {} seconds.".format(sleep_time))
            time.sleep(sleep_time)
        else:
            no_task_found = []
            print("{} processing task {}.".format(verifier_name, reserved_task_key))
            #time.sleep(1)
            # delete the task
            delete_task(reserved_task_key, task)
            


def keep_creating_problems():
    total_created = 0
    start = time.time()
    plenty_of_problems = 0
    while True:
        # Fetch total problems 
        tasks = fetch_tasks()
        if tasks == None:
            tasks = {}
            
        numTasks = len(tasks.keys())
        if numTasks < num_users:
            plenty_of_problems = 0
            now = time.time()
            elapsed_time = now - start
            average_time = 1 
            if total_created > 0:
                average_time = round(elapsed_time / total_created,2)
            print("There were only {}. Adding another problem for total of {} and {} seconds per problem..".format(numTasks,total_created, average_time))
            create_task()
            create_task()
            create_task()
            create_task()
            total_created += 4
        else:
            if plenty_of_problems < 10: 
                plenty_of_problems += 1  
            print("Sleeping {} seconds.".format(plenty_of_problems))
            time.sleep(plenty_of_problems)
            
# Start main loops        
if create_problems: 
    keep_creating_problems() 
else: 
    keep_solving_problems()       


#result = create_task()
#print(result)

# Select non-reserved task
# Process task
# Log task results
# Enable parrallel reservation and processing using versioning rule.
# Try without transactions
# http://stackoverflow.com/questions/23041800/firebase-transactions-via-rest-api
 
"""
Test Case: 
Load generator simulating 1 to n users adding verification requests to the queue. 
TestUsers could have an auth_key(s) that allow it to simulate from 1 to n users. 
2 servers running 2 cores each is the test case to test scale-out and scale-up. 
Solve the concurrency issues before solving the authorization issues. 
Having a server on AWS, DigitalOcean, and your local system all running at once is the next use case. 
Then you can put all security in place. 

"""
  
# Add security rules for queue. 

# Grab abandoned reserved tasks

#result = create_task()
#print(result)

#result = reserve_task(result['name'])
#print(result)

#tasks = fetch_tasks()
