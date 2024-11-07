import argparse
from ruamel.yaml import YAML
import tempfile
import shutil
import boto3
import os


# Define constructors for CloudFormation-specific tags
def ref_constructor(loader, node):
    return {"Ref": loader.construct_scalar(node)}


def get_att_constructor(loader, node):
    return {"Fn::GetAtt": loader.construct_scalar(node)}


def load_yaml(file_path):
    """Load the YAML file."""
    with open(file_path, 'r') as file:
        return yaml.load(file)


def save_yaml(data, file_path):
    """Save data to the YAML file."""
    with open(file_path, 'w') as file:
        yaml.dump(data, file)


def format_parameters(params_dict):
    """Convert parameters dictionary to AWS CloudFormation-compatible format."""
    return [{"ParameterKey": key, "ParameterValue": str(value)} for key, value in params_dict.items()]


def update_yaml(file_path, name=None, size=None):
    """Update YAML file with new parameters."""
    # Load existing YAML data
    data = load_yaml(file_path)
    # print(data['Parameters']['ASGName'])
    # Update the parameters if provided
    if name:
        data['Resources']['MyAutoScalingGroup']['Properties']['AutoScalingGroupName'] = name
        data['Outputs']['AutoScalingGroupID']['Value']['Ref'] = name
    if size is not None:
        data['Resources']['MyAutoScalingGroup']['DesiredCapacity'] = size

    # Create a temporary backup of the original file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        shutil.copyfile(file_path, temp_file.name)

    try:
        # Save updated YAML data to the file
        save_yaml(data, file_path)
        print(f"Updated YAML file '{file_path}' successfully.")
    except Exception as e:
        # If something goes wrong, restore the original file
        shutil.move(temp_file.name, file_path)
        print(f"Failed to update YAML file. Restored original file. Error: {e}")
    finally:
        # Clean up the temporary file if it still exists
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)


def upload_to_s3(file_path, bucket_name, object_name):
    """Upload the YAML file to S3 and return the S3 URL."""
    try:
        s3.upload_file(file_path, bucket_name, object_name)
        # Return the S3 URL after the upload is complete
        return f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        raise


def deploy_stack(yaml_config, s3_url, template_url, stack_name_param = 'default'):
    # Initialize CloudFormation client
    cloudformation = boto3.client('cloudformation', region_name='us-west-2')
    
    # Extracting values from YAML configuration
    stack_name = stack_name_param
    template_url = template_url
    parameters = format_parameters(yaml_config['Parameters'])
    
    try:
        # Check if stack exists
        response = cloudformation.describe_stacks(StackName=stack_name)
        stack_exists = True
    except cloudformation.exceptions.ClientError:
        stack_exists = False

    if stack_exists:
        # Update stack if it already exists
        print(f"Updating stack: {stack_name}")
        response = cloudformation.update_stack(
            StackName=stack_name,
            TemplateURL=s3_url,
            Parameters=parameters,
            Capabilities=['CAPABILITY_IAM']
        )
    else:
        # Create stack if it doesn't exist
        print(f"Creating stack: {stack_name}")
        response = cloudformation.create_stack(
            StackName=stack_name,
            TemplateURL=s3_url,
            Parameters=parameters,
            Capabilities=['CAPABILITY_IAM']
        )

    print("Stack operation initiated, waiting for completion...")
    waiter = cloudformation.get_waiter('stack_create_complete' if not stack_exists else 'stack_update_complete')
    waiter.wait(StackName=stack_name)
    print("Stack operation completed successfully.")
    return response


if __name__ == "__main__":
    yaml = YAML()
    yaml.Constructor.add_constructor("!Ref", ref_constructor)
    yaml.Constructor.add_constructor("!GetAtt", get_att_constructor)
    parser = argparse.ArgumentParser(description="Update parameters in a YAML file.")
    parser.add_argument("yaml_file", help="Path to the YAML file to be updated.")
    parser.add_argument("-n", "--name", help="Set the name for the Auto Scaling Group (ASG).")
    parser.add_argument("-s", "--size", type=int, help="Set the number of instances for the ASG.")
    parser.add_argument("-sn", "--stackName", help="Set the stack name for the ASG.")
    parser.add_argument("-b", "--bucketName", help="The name of the S3 bucket where the YAML template will be uploaded.", required=True)
    
    args = parser.parse_args()

    # Check if YAML file and stack name are provided
    if not args.yaml_file:
        raise ValueError("YAML file path is required. Please provide the YAML file with -f or --yaml_file argument.")
    
    if not args.stackName:
        raise ValueError("Stack name is required. Please provide the stack name with -sn or --stackName argument.")

    # Update YAML with provided command-line arguments
    update_yaml(args.yaml_file, name=args.name, size=args.size)

    yaml_config = load_yaml(args.yaml_file)

    # Initialize AWS S3
    s3 = boto3.client('s3', region_name='us-west-2')
    # Upload the YAML file to S3
    s3_url = upload_to_s3(args.yaml_file, args.bucketName, os.path.basename(args.yaml_file))

    # Deploy the stack
    response = deploy_stack(yaml_config, s3_url, template_url=args.yaml_file, stack_name_param=args.stackName)
    print("Stack operation response:", response)


