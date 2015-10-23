# This is an example verifier to simplify docker testing and development. 
# Verifiers can not print() to standard out since everything printed is going to back to the 
# caller as a json string. Include debug information if you want to be able to monitor and debug 
# variables in the container. Extra keys in solutions will just be ignored. 
import sys
import os
import json

def get_results():
	#Read the solution. If pass then pass. 
	cwd = os.getcwd()
	
	#Find the solution text in the data folder and examine it to return true for false for solved. 
	target = 'data/solution.txt'
	solution_text = ""
	if os.path.exists(target):
		with open(target) as data_file:    
			solution_text = data_file.read()

    # Setup a default result. 
	results = {"run_time":7,"solved":True,"results":[],"run_count":1}
	
	# Make the result solved=False if the solution contains the text "fail"
	if "fail" in solution_text:
		results["solved"] = False
	elif "error" in solution_text:
		results = {"errors": "This is an example of an error."}
		
	return json.dumps(results)

if __name__ == '__main__':
    sys.stdout.write("{}\n".format(get_results()))
	#exit(get_results()) 

