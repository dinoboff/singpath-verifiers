# This script downloads problem examples and runs them in a container.
# The initial development runs examples in a local directory until container execution can be implemented.  
import json
import os
import sys
from sys import platform as _platform

"""
This script will mainly write out each problem and solution, run the docker verify command, collect the solution, 
and then compare the results.
You should be able to check all of the docker verifiers at once. 

There can be 2 scripts - run all of these from subfolders on the local machine. 
Then one to run all of the problem in their docker containers. 
"""
# We need to add sudo when running docker on linux systems. 
dstart = ""
if _platform=='linux2': 
    dstart = "sudo "

run_local = False

if len(sys.argv) > 1 and sys.argv[1]=='local':
    print("Testing locally.")
    run_local = True

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
        
def run_secure_verifier(directory):
    if run_local:
        # Test the verify.py scripts for each language in local subdirectories on a test system. 
        savedPath = os.getcwd()
        os.chdir(directory)
        os.system('python verify.py')
        os.chdir(savedPath)
        
    else: 
        local_dir = os.getcwd()+"/"+directory
        # Find the container to download and use when calling docker run. 
        docker_container = docker_verifier_images[directory]["image"]
        command = docker_verifier_images[directory]["command"]
        remote_dir = "data"
        #print("Under development. Mounting directory {} to remote directory  {}".format(local_dir, remote_dir))
       
        # We will assume that all verifier containers will support python and call the verify.py created for each language. 
        
        docker_command = dstart +'docker run -v '+local_dir+':/data '+docker_container+' '+command

        # Will call Docker using subprocess and capture the output. 
        # Todo: handle errors and support timeouts. 
        print("Running command -> {}".format(docker_command))
        import subprocess
        try: 
            result = subprocess.check_output(docker_command, shell=True)
            data = json.loads(result.decode())
        except: 
            data = {"errors": "An error occurred when calling the verifier. {}".format(str("TBD"))}   
        
        print("The result returned from the verifier was {}".format(data))
        return data
 
    
def read_results(directory):
    target = directory+'/results.json'
    if os.path.exists(target):
        with open(target) as data_file:    
            results = json.load(data_file)
        return results
    else: 
        # Write out a no results returned error. 
        data = {"solved":False, 
                "results": [["Verifier did not return a result", 0, compile_result, "fail"]]}
        with open("results.json", 'w') as outfile:
            json.dump(data, outfile) 

# Load problem examples
with open('problem_examples.json') as data_file:    
    examples = json.load(data_file)

# Iterterate through each language and call the language verify.py in each directory. 
test_results = {}
for language in examples.keys():
  if not "language" in test_results.keys():
      test_results[language] = []  
  for key in examples[language].keys():
    example = examples[language][key]
    # write out problem.txt and tests.txt in the target directory. 
    write_solution(example['solution'], directory=language)
    write_test(example['tests'],  directory=language)
    
    # run the verifier. 
    result = run_secure_verifier( directory=language)
    #result = read_results( directory=language)
    
    if "solved" in result:
        if result['solved'] != example['is_solved']:
    
            test_results[language].append("Failed - {} expected {} recieved {}.".format(key,example['is_solved'],result['solved']))
        else:
            test_results[language].append("Passed {} -> {}".format(language, key))
    elif "errors" in result:
        if "returns_error" in example:
            test_results[language].append("Passed {} -> {}".format(language, key))
        else:
            test_results[language].append("Unexpected errors returned {} -> {}".format(language,key))
    else: 
        test_results[language].append("The verifier did not return solved or errors {} -> {}".format(language, key))
        

print("-----------------")
print("Problem Examples Test Results")
for language in test_results.keys(): 
    for result in test_results[language]: 
        print(result)


