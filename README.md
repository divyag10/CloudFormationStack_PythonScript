# CloudFormationStack_PythonScript
Python script to provisions the Auto Scaling Group on AWS Cloud, using CloudFormation template.


## launchTemplate.yaml: 
Cloud formation template to provision Launch Template, uses t3.micro instance and also provisions security group.

## ASGTemplate.yaml: 
Cloud formation template to provision Auto Scaling Group, which uses Launch Template.

## ScriptASGCreate.py:
This is a Python script that takes various arguments, mentioned below and provisions the ASG on AWS Cloud. Follow below steps to run the script.

### Installations required:
- Pip install boto3
- Pip install ruamel.yaml
- Pip install awscli

### To run python script, pass following args:
- Required: Path to Cloud formation yaml for ASG.
- -n NAME, to Set the name for the Auto Scaling Group (ASG).
- -s SIZE, to Set the number of instances for the ASG.
- -sn, to Set the stack name for the ASG.
- -b, The name of the S3 bucket where the YAML template will be uploaded. 
- Also, configure the AWS credentials using AWS CLI, by giving command :  aws configure

**P.S.:** If you wish to run script multiple times, you will have to clean the resources as same name resource would have been created in your account and it would throw error as Stack creation failed.

