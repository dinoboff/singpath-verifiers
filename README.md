# singpath-verifiers
The docker-based verifiers that support SingPath.com

You can launch an Amazon Linux image on EC2 to quickly test all the current verifiers. The following steps need to be run after you launch a starndare Amazon micro-instance image. 

sudo yum install docker
sudo service docker start
sudo yum install git
git clone https://github.com/ChrisBoesch/singpath-verifiers.git
cd singpath-verifiers
python test_all_verifiers.py

The test_all_verifiers.py script will run through all of the examples found in problem_examples.json. 

This test script tries to verify the solution with each provided test. If the needed docker image is not present, the docker image is downloaded by docker before the code is verified. The test script writes the solution and tests into a local folder and then mounts that folder so that the docker container can view the solution.txt and tests.txt files. Verifiers for each language then run in their own Docker containers and return results in the JSON format: 

Here is a passing example with solved==True
{'results': [{'expected': 2, 'call': 'x', 'correct': True, 'received': '2'}], 'printed': '99\n', 'solved': True}

And here is an example with a passing tests and failing test. 

{'results': [{'call': 'x', 'expected': 2, 'received': '2', 'correct': True}, 
             {'call': 'y', 'expected': 3, 'received': '2', 'correct': False}],
'printed': '', 
'solved': False,}


These results from verifying code are usually used to build a table to provide feedback to users. 

| Called | Expected | Recieved  | Correct |
| ------ |:--------:| :--------:|:--------|
| x      | 2        | 2         | True    |
| y      | 3        | 2         | False   |







