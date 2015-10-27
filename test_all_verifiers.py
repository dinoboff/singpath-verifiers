# This script downloads problem examples and runs them in a container.
# The initial development runs examples in a local directory until container execution can be implemented.  
import json
import os
import sys
from sys import platform as _platform
import shutil
import datetime

"""
This script will mainly write out each problem and solution, run the docker verify command, collect the solution, 
and then compare the results.
You should be able to check all of the docker verifiers at once. 

Todo: 
    run the languages in parrallel. 
    next look at running 2 copies of each language in parrallel in subfolders. (java-1, java-2)
"""
parallelism = 1
if len(sys.argv) > 1:
    parallelism = int(sys.argv[1])
    print("Running in parallel with parallelism {}".format(parallelism))
    
MAX_SECONDS = 30

# We need to add sudo when running docker on linux systems. 
dstart = ""
if _platform=='linux2': 
    dstart = "sudo "

    
docker_verifier_images = {}
docker_verifier_images['example']= {"image":"library/python","command":"python data/verify.py"}
docker_verifier_images['python']= {"image":"library/python","command":"python data/verify.py"}
docker_verifier_images['java']= {"image":"library/java","command":"python data/verify.py"}
docker_verifier_images['javascript']= {"image":"node","command":"node data/verify.js"}

# Write out tests from string
def write_solution(solution_code,  directory):        
    with open(directory+'/solution.txt', 'w') as the_file:
        the_file.write(solution_code)
        
def write_test(test_code, directory):
    with open(directory+'/tests.txt', 'w') as the_file:
        the_file.write(test_code)
        
def run_secure_verifier(directory, language):
        local_dir = os.getcwd()+"/"+directory
        # Find the container to download and use when calling docker run. 
        docker_container = docker_verifier_images[language]["image"]
        command = docker_verifier_images[language]["command"]
        remote_dir = "data"

        # Read only host folder
        docker_command = dstart +'docker run -v '+local_dir+':/data:ro '+docker_container+' '+command
        #docker_command = dstart +'docker run -v '+local_dir+':/data '+docker_container+' '+command

        # Will call Docker using subprocess and capture the output. 
        # Todo: handle errors and support timeouts. 
        print("Running command -> {}".format(docker_command))
        import subprocess
        
        # This will need to be returned to run in parallel. 
        result = None
        try:
           result = subprocess.check_output(docker_command, shell=True, timeout=MAX_SECONDS)
        except:   
           result = "TIMEOUT" 
    
        data = None
        if result == "TIMEOUT":
            data = {"errors": "Code took too long to run. {}".format(str("TBD"))}

        else: 
            try:
                data = json.loads(result.decode())
            except:
                data = {"errors": "An error occurred when calling the verifier. {}".format(str("TBD"))}   
                    
        print("The result returned from the verifier was {}".format(data))
        return data
 
# Load problem examples
with open('problem_examples.json') as data_file:    
    examples = json.load(data_file)

def setup_and_verify(language, key):
    # Run all of this in parallel in threads. 
    working_directory = language+"_"+key
    # copy all files to a new directory. 
    # delete the working directory if it exists. 
    if os.path.isdir(working_directory):
        shutil.rmtree(working_directory)
    
    shutil.copytree(language,working_directory)
    
    example = examples[language][key]
    # write out problem.txt and tests.txt in the target directory. 
    write_solution(example['solution'], directory=working_directory)
    
    write_test(example['tests'],  directory=working_directory)
    
    # run the verifier. 
    result = run_secure_verifier( directory=working_directory, language=language)
    
    # Remove the temporary working directory. 
    if os.path.isdir(working_directory):
        shutil.rmtree(working_directory)
    
    if "solved" in result:
        if result['solved'] != example['is_solved']:
    
            test_results[language].append("**Failed** - {} expected {} recieved {}.".format(key,example['is_solved'],result['solved']))
        else:
            test_results[language].append("Passed {} -> {}".format(language, key))
    elif "errors" in result:
        if "returns_error" in example:
            test_results[language].append("Passed {} -> {}".format(language, key))
        else:
            test_results[language].append("Unexpected errors returned {} -> {}".format(language,key))
    else: 
        test_results[language].append("The verifier did not return solved or errors {} -> {}".format(language, key))

def func1(a,b):
    print(a+"->"+b)
    
# Iterterate through each language and call the language verify.py in each directory. 
test_results = {}

#Create working directories with name language-problemkey
start_time = datetime.datetime.now()

threads = []

for language in examples.keys():
  if not "language" in test_results.keys():
      test_results[language] = []  
  for key in examples[language].keys():
      
      # This needs to be run in parallel. 
      import threading
      t1 = threading.Thread(target=setup_and_verify, args=(language, key))
      #t1.start()
      threads.append(t1)
      #t1.join()
 
# We can pace how many threads are started and active at any given time.  
print("Running with parallelism {}".format(parallelism)) 
blocks = len(threads)/parallelism
while len(threads) >= parallelism:
    print("Total threads = {}".format(len(threads)))
    for x in range(parallelism):
        threads[x].start()

    for x in range(parallelism):
        threads[x].join()
    
    for x in range(parallelism):
        del threads[0]

# Clean up remaining threads
if len(threads) > 0:
    print("Cleaning up. Total threads = {}".format(len(threads)))
    for x in range(len(threads)):
        threads[x].start()
    for x in range(len(threads)):
        threads[x].join() 
    for x in range(len(threads)):
        del threads[0]   

stop_time = datetime.datetime.now()        

print("-----------------")
print("Problem Examples Test Results")
for language in test_results.keys(): 
    for result in test_results[language]: 
        print(result)
print()
print("Running all tests took {}.".format(stop_time - start_time))

