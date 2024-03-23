# Import necessary libraries and modules
from datetime import datetime, timezone
import concurrent.futures
import sys
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import boto3

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamo_client = boto3.client('dynamodb')
sts_client = boto3.client('sts',region_name='eu-west-2')

# Initialize global variables
item_list = []
acc_list = []
t = datetime.now(timezone.utc)
today=t.strftime('%Y-%m-%d')
save_path = '/tmp/'
filename = save_path+'LM_AWS_Services_Inventory-'+today+'.csv'

# Lambda function handler
def lambda_handler(event,  context):
    MemberRoleTable = os.environ["MEMBER_ROLE_TABLE"]
    paginator = dynamo_client.get_paginator("scan")
    # Use DynamoDB paginator to scan items in a table
    for page in paginator.paginate(TableName=MemberRoleTable):
        for item in page['Items']:
            item_list.append(item)
    # Call the main function with the fetched items
    main(item_list)  

# Main function to orchestrate the process
def main(item_list):
    print("Please wait while we fetch the Inventory info and save it to Inventory-date.csv....")
    print('AccountName','','StartTime','','EndTime')
    # Use ThreadPoolExecutor for parallel execution of functions
    with concurrent.futures.ThreadPoolExecutor() as g:
        _acclist=[]
        for item in item_list:
            _acclist.append(g.submit(get_service_count,item))
        for r in concurrent.futures.as_completed(_acclist):
            pass
    # Perform file operations and upload the report
    file_name=filename
    print("Preparing the report")
    get_report(file_name)
    print("Uploading the report to s3 bucket")
    upload_file(file_name)
    print("Uploaded the report to s3 bucket. Updating the DynamoDB Table")
    update_dd_table()
    print("Updated the DynamoDB Table. Sending email to the recepient")
    send_email_with_attachment(file_name)

# Function to get service count for each AWS account    
def get_service_count(item):
    # Extract relevant information from the item     
    indx = item['S No.']['N']
    AccountName = item['Account Name']['S']
    region = item['Region']['S']
    rolearn = item['Role Arn']['S']
    AccountId = item['Account ID']['S']
    try:
        # Assume role to get temporary credentials
        assumed_role = sts_client.assume_role(
                    RoleArn=str(rolearn),
                    RoleSessionName='session')
                    
        credentials=assumed_role['Credentials']
        ACCESS_KEY = credentials['AccessKeyId']
        SECRET_KEY = credentials['SecretAccessKey']
        SESSION_TOKEN = credentials['SessionToken']            
        # Record the start time
        now = datetime.now()
        start = now.strftime("%H:%M:%S")
        # Create a dictionary to store service counts
        dict = {}
        # Use ThreadPoolExecutor for parallel execution of service count functions
        with concurrent.futures.ThreadPoolExecutor() as e:
            _list=[]
            # Append service count functions to the list
            _list.append(e.submit(s3_count, ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit(rds_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit(ec2_count,AccountName,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit(elb_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit(asg_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit(efs_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit(fsx_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit(lambda_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit(kms_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( cert_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( secrect_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( sns_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( sfn_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( dynamo_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( direct_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( vpc_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( vpn_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( tgw_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( r53_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( cloudfront_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( waf_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN) )
            _list.append(e.submit( directories_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( stack_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( eks_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( ecs_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( sqs_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( rshift_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( sgw_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            _list.append(e.submit( iam_user_count,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN))
            for r in concurrent.futures.as_completed(_list):
                dict.update(r.result())
        # Create a dictionary for account details
        acc_dict = {}
        acc_dict['S No.']           = indx
        acc_dict['AccountName']     = AccountName 
        acc_dict['AccountId']       = AccountId    
        acc_dict['Region']          = region         
        acc_dict['s3']              = dict.get('s3')        
        acc_dict['rds']             = dict.get('rds')
        acc_dict['ec2']             = dict.get('ec2')
        acc_dict['elb']             = dict.get('elb')
        acc_dict['asg']             = dict.get('asg')
        acc_dict['efs']             = dict.get('efs')
        acc_dict['fsx']             = dict.get('fsx') 
        acc_dict['lmbda']           = dict.get('lambda') 
        acc_dict['kms']             = dict.get('kms')   
        acc_dict['cert']            = dict.get('cert')   
        acc_dict['secret']          = dict.get('secret') 
        acc_dict['sns']             = dict.get('sns')
        acc_dict['sfn']             = dict.get('sfn')
        acc_dict['dynamo']          = dict.get('dynamo')
        acc_dict['direct']          = dict.get('direct_connect')
        acc_dict['vpc']             = dict.get('vpc')
        acc_dict['vpn']             = dict.get('vpn')
        acc_dict['tgw']             = dict.get('tgw')
        acc_dict['cloudfront']      = dict.get('cfront')
        acc_dict['waf']             = dict.get('waf')
        acc_dict['directory']       = dict.get('directory')
        acc_dict['stack']           = dict.get('stack')
        acc_dict['eks']             = dict.get('eks')
        acc_dict['ecs']             = dict.get('ecs')
        acc_dict['r53']             = dict.get('r53')
        acc_dict['sqs']             = dict.get('sqs')
        acc_dict['rshift']          = dict.get('rsh')
        acc_dict['sgw']             = dict.get('Storage')
        acc_dict['iam_users'] = dict.get('iam_users')
        # Append the account dictionary to the list
        acc_list.append(acc_dict)
        # Record the end time and print account details
        now = datetime.now()
        End = now.strftime("%H:%M:%S")
        print(AccountName,'',start,'',End)
    except:
        print("Error in account logging in :",AccountName)              
        err = PrintException()
        print(err)

# Generate the CSV report
def get_report(file_name):
    with open(file_name, 'w') as f:
        print("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % 
              ('Account Name','Account ID','Region','S3','RDS','Ec2','ELB','ASG','EFS','FSX','Lambda','KMS','Cert','Secrets','SNS','SQS','StepFunction','DynamoDB','Direct Connect',
               'VPC','VPN','Transit Gateway','R53','Cloudfront','WAF','Directory Service','CloudFormation','EKS','ECS','Redshift','SGW','Forecast','IAM Users'),file=f)
        for acc_dict in acc_list:
            print("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % 
                  (acc_dict['AccountName'],acc_dict['AccountId'],acc_dict['Region'],acc_dict['s3'],acc_dict['rds'],acc_dict['ec2'],acc_dict['elb'],acc_dict['asg'],acc_dict['efs'],acc_dict['fsx'],acc_dict['lmbda'],acc_dict['kms'],acc_dict['cert'],acc_dict['secret'],acc_dict['sns'],acc_dict['sqs'],
                   acc_dict['sfn'],acc_dict['dynamo'],acc_dict['direct'],acc_dict['vpc'],acc_dict['vpn'],acc_dict['tgw'],acc_dict['r53'],acc_dict['cloudfront'],acc_dict['waf'],acc_dict['directory'],acc_dict['stack'],acc_dict['eks'],acc_dict['ecs'],acc_dict['rshift'],acc_dict['sgw'],'0',acc_dict['iam_users']),file=f)

# Update DynamoDB table with Service count information for each account
def update_dd_table():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ["AWS_SERVICES_INVENTORY_DYNAMODB_TABLE"])
    for acc_dict in acc_list:
        try:
            response = table.put_item(Item={
            'S No.':acc_dict['S No.'],              
            'AccountName':acc_dict['AccountName'],  
            'AccountId': acc_dict['AccountId'],
            'Region':acc_dict['Region'],
            'S3':acc_dict['s3'],
            'RDS':acc_dict['rds'],
            'EC2':acc_dict['ec2'],
            'ELB':acc_dict['elb'],
            'ASG':acc_dict['asg'],
            'EFS':acc_dict['efs'],
            'FSX':acc_dict['fsx'],
            'Lambda':acc_dict['lmbda'],
            'KMS Keys':acc_dict['kms'],
            'Certificates':acc_dict['cert'],
            'Secrets':acc_dict['secret'],
            'SNS':acc_dict['sns'],
            'StepFunctions':acc_dict['sfn'],
            'DynamoDB':acc_dict['dynamo'],
            'Direct Connect':acc_dict['direct'],
            'VPC':acc_dict['vpc'],
            'VPN':acc_dict['vpn'],
            'Transit GW':acc_dict['tgw'],
            'CloudFront':acc_dict['cloudfront'],
            'WAF':acc_dict['waf'],
            'Directory':acc_dict['directory'],
            'CloudFormation Stacks':acc_dict['stack'],
            'EKS':acc_dict['eks'],
            'ECS':acc_dict['ecs'],
            'Route 53':acc_dict['r53'],
            'SQS':acc_dict['sqs'],
            'RedShift':acc_dict['rshift'],
            'Storage GW':acc_dict['sgw'],
            'IAM Users' : acc_dict['iam_users']
                } 
                )
        except:
            print(PrintException())
            print("Error during table.put_item")
            response = "Error"

# Funtion to find the count of Native IAM users          
def iam_user_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    user_list = []
    iam_client = boto3.client('iam',
                            aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN
                                )
    iam_response = iam_client.list_users()
    for user in iam_response['Users']:
        user_arn = user['Arn']
        user_list.append(user_arn)
    return {'iam_users': len(user_list)}   

# Funtion to find the count of total S3 buckets in the region
def s3_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    s3list = []
    client = boto3.client('s3',
                            aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN
                                )
    response = client.list_buckets()
    if response:
        for bucket in response['Buckets']:
            s3list.append(bucket['Name'])
    
    return {'s3': len(s3list)}

# Funtion to find the count of RDS databases
def rds_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    rdslist = []
    client = boto3.client('rds',
                            aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.describe_db_instances()
    if response:
        for rds in response['DBInstances']:
            rdslist.append(rds['DBInstanceIdentifier'])

    return {'rds': len(rdslist)}

# Funtion to find the count of AWS Redshift Clusters
def rshift_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    rshiftlist = []
    client = boto3.client('redshift',
                            aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.describe_clusters()
    if response:
        for rshift in response['Clusters']:
            rshiftlist.append(rshift['ClusterIdentifier'])

    return {'rsh': len(rshiftlist)}

# Funtion to find the count of EC2 Servers
def ec2_count(AccountName,ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    ec2list = []
    client = boto3.client('ec2',
                            aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    try:
        response = client.describe_instances()
    except:
        err = PrintException()
        print(err)
    if response:
        for r in response['Reservations']:
            for instance in r['Instances']:
                ec2list.append(instance['InstanceId'])
    return {'ec2': len(ec2list)}

# Funtion to find the count of Elastic Load Balancers
def elb_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    elblist = []
    client = boto3.client('elbv2',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.describe_load_balancers()
    if response:
        for elb in response['LoadBalancers']:
            elblist.append(elb['LoadBalancerName'])

    return {'elb': len(elblist)}

# Funtion to find the count of total Autoscaling group
def asg_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    asglist = []
    client = boto3.client('autoscaling',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.describe_auto_scaling_groups()
    if response:
        for asg in response['AutoScalingGroups']:
            asglist.append(asg['AutoScalingGroupARN'])

    return {'asg': len(asglist)}

# Funtion to find the count of elastic file systems
def efs_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    efslist = []
    client = boto3.client('efs',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.describe_file_systems()
    if response:
        for efs in response['FileSystems']:
            efslist.append(efs['FileSystemId'])
        
    return {'efs': len(efslist)}

# Funtion to find the count of File Servers
def fsx_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    fsxlist = []
    client = boto3.client('fsx',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.describe_file_systems()
    if response:
        for fsx in response['FileSystems']:
            fsxlist.append(fsx['FileSystemId'])
        
    return {'fsx': len(fsxlist)}

# Funtion to find the count of keys stored in Key Management Service
def kms_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    keylist = []
    client = boto3.client('kms',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.list_keys(Limit=1000)
    if response:
        for keys in response['Keys']:
            keylist.append(keys['KeyArn'])
        
    return {'kms': len(keylist)}

# Funtion to find the count of Lambda functions
def lambda_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    lambdalist = []
    client = boto3.client('lambda',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.list_functions(MaxItems=50)
    for lmbda in response['Functions']:
        lambdalist.append(lmbda['FunctionArn'])

    while 'NextMarker' in response:
        response = client.list_functions(Marker=response['NextMarker'],MaxItems=50)
        for lmbda in response['Functions']:
            lambdalist.append(lmbda['FunctionArn'])

    return {'lambda': len(lambdalist)}

# Funtion to find the count of ACM certificates
def cert_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    certlist = []
    client = boto3.client('acm',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.list_certificates()
    if response:
        for cert in response['CertificateSummaryList']:
            certlist.append(cert['CertificateArn'])
        
    return {'cert': len(certlist)}

# Funtion to find the count of Secrets stored in AWS Secrets Manager
def secrect_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    seclist = []
    client = boto3.client('secretsmanager',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.list_secrets(MaxResults=100)
    if response:
        for sec in response['SecretList']:
            seclist.append(sec['ARN'])
    
    return {'secret': len(seclist)}

# Funtion to find the count of Queues in AWS SQS
def sqs_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    sqslist = []
    client = boto3.client('sqs',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.list_queues()
    if 'QueueUrls' in response:
        for queue in response['QueueUrls']:
            sqslist.append(queue)

    return {'sqs': len(sqslist)}

# Funtion to find the count of Secure Gateway id
def sgw_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    sgwlist = []
    client = boto3.client('storagegateway',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.list_gateways()
    if response:
        for sgw in response['Gateways']:
            sgwlist.append(sgw['GatewayId'])
    return {'Storage': len(sgwlist)}

# Funtion to find the count of Topic in AWS SNS
def sns_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    snslist = []
    client = boto3.client('sns',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.list_topics()
    if response:
        for topic in response['Topics']:
            snslist.append(topic['TopicArn'])

    return {'sns': len(snslist)}

# Funtion to find the count of State Machines in AWS Step Functions
def sfn_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    steplist = []
    client = boto3.client('stepfunctions',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.list_state_machines()
    if response:
        for state in response['stateMachines']:
            steplist.append(state['stateMachineArn'])
        
    return {'sfn': len(steplist)}

# Funtion to find the count of AWS Dynamo DB tables
def dynamo_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    dylist = []
    client = boto3.client('dynamodb',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.list_tables()
    if response:
        for state in response['TableNames']:
            dylist.append(state)
    return {'dynamo': len(dylist)}

# Funtion to find the count of connetions for AWS Direct Connect
def direct_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    dclist = []
    client = boto3.client('directconnect',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)

    response = client.describe_connections()
    if response:
        for connect in response['connections']:
            dclist.append(connect['connectionId'])
        
    return {'direct_connect': len(dclist)}

# Funtion to find the count of VPC's
def vpc_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    vpclist = []
    client = boto3.client('ec2',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.describe_vpcs()
    if response:
        for vpc in response['Vpcs']:
            vpclist.append(vpc['VpcId'])
        
    return {'vpc': len(vpclist)}

# Funtion to find the count of Site to Site VPN connections
def vpn_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    vpnlist = []
    client = boto3.client('ec2',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.describe_vpn_connections()
    if response:
        for vpn in response['VpnConnections']:
            vpnlist.append(vpn['VpnConnectionId'])
        
    return {'vpn': len(vpnlist)}

# Funtion to find the count of Transit Gateway's
def tgw_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    tgwlist = []
    client = boto3.client('ec2',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.describe_transit_gateways()
    if response:
        for tgw in response['TransitGateways']:
            tgwlist.append(tgw['TransitGatewayId'])
        
    return {'tgw': len(tgwlist)}

# Funtion to find the count of Hosted Zones in AWS Route 53
def r53_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    r53list = []
    client = boto3.client('route53',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)

    response = client.list_hosted_zones(MaxItems='50')
    if response:
        for r53 in response['HostedZones']:
            r53list.append(r53['Name'])

        while 'NextMarker' in response:
            response = client.list_hosted_zones(Marker=response['NextMarker'],MaxItems='50')
            for r53 in response['HostedZones']:
                r53list.append(r53['Name'])

    return {'r53': len(r53list)}

# Funtion to find the count of Distribution list in AWS Cloudfront
def cloudfront_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    cloudfrontlist = []
    client = boto3.client('cloudfront',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)

    response = client.list_distributions()
    if response:
        if response['DistributionList']['Quantity'] == 0:
            pass
        else:
            for cf in response['DistributionList']:
                if cf == 'Quantity':
                    cloudfrontlist.append(cf)
          
    return {'cfront': len(cloudfrontlist)}

# Funtion to find the count of WebACL's in AWS WAF
def waf_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    waflist = []
    client = boto3.client('waf',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.list_web_acls()
    if response:
        for web in response['WebACLs']:
            waflist.append(web['WebACLId'])  
    
    return {'waf': len(waflist)}

# Funtion to find the count of Directories irrespective of AD type
def directories_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    dslist = []
    client = boto3.client('ds',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.describe_directories()
    if response:
        for direc in response['DirectoryDescriptions']:
            dslist.append(direc['DirectoryId'])
        
    return {'directory': len(dslist)}

# Funtion to find the count of Stacks in AWS Cloudformation
def stack_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    stacklist = []
    client = boto3.client('cloudformation',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.list_stacks()
    for stack in response['StackSummaries']:
        stacklist.append(stack['StackName'])

    while 'NextToken' in response:
        response = client.list_stacks(NextToken=response['NextToken'])
        for stack in response['StackSummaries']:
            stacklist.append(stack['StackName'])
    
    return {'stack': len(stacklist)}

# Funtion to find the count of Container clusters in AWS ECS
def ecs_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    ecslist = []
    client = boto3.client('ecs',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.list_clusters()
    if response:
        for cluster in response['clusterArns']:
            ecslist.append(cluster)

    return {'ecs': len(ecslist)}

# Funtion to find the count of EKS Clusters in AWS EKS service
def eks_count(ACCESS_KEY,SECRET_KEY,region,SESSION_TOKEN):
    ekslist = []
    client = boto3.client('eks',aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=region,aws_session_token=SESSION_TOKEN)
    response = client.list_clusters()
    if response:
        for cluster in response['clusters']:
            ekslist.append(cluster)

    return {'eks': len(ekslist)}

# Upload the report to S3
def upload_file(file_name):
    import datetime
    mydate = datetime.datetime.now()
    Month=mydate.strftime("%B")
    bucket=os.environ["REPORTING_AUTOMATION_BUCKET"]
    object_name='Reports_'+Month+'/'+'LM_AWS_Inventory/'+file_name
    object_name = object_name.replace(save_path,"")

    # Upload the file
    s3 = boto3.resource('s3')
    try:
        response = s3.meta.client.upload_file(file_name, bucket, object_name)
    except:
        err = PrintException()
        print(err)

# Format HTML content for email body
def format_html():
    BODY_HTML = """	<html>
        <head><style>table, th, td { border: 1px solid black;}</style></head>
        <body>
        <p style="font-weight: bold; font-size: 20px; color: red;">LM AWS Services Inventory</p>
        <p>Hi All,</p>
        <p>     PFA report containing AWS Services Inventory report.</p>
        <p>"""
    
    BODY_Content = BODY_HTML 
    BODY_Content = BODY_Content + """ </p><br>
                  <p>Best Regards,<br>
                  AWS Services Inventory Lambda<br>
                  LM CloudOps Automation OBO Sathya Pradeep C
                  </body>
                  </html> """
    return BODY_Content

def send_email_with_attachment(file_name):
    # Send email with the generated report attached
    print('Sending the Report to the team..')
    BODY_TEXT = format_html()
    CHARSET = "utf-8"

    # Set message body
    msg = MIMEMultipart('mixed')
    msg["Subject"] = "LM_CloudOps_Automation : AWS Services Inventory"
    bmsg_body = MIMEMultipart('alternative')
    htmlpart = MIMEText(BODY_TEXT, 'html', CHARSET)
    bmsg_body.attach(htmlpart)

    # Attach the file with a sanitized filename
    sanitized_filename = file_name.replace(save_path, '').replace(":", "-")
    with open(file_name, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={sanitized_filename}")
        msg.attach(part)
    
    # Attach HTML content
    msg.attach(bmsg_body)

    # Debugging: Print the message before sending
    print("Debug: Message before sending")
    print(msg.as_string())

    #Fetching sender and receiver email from ENV Variables
    SENDER = os.environ["SENDER_LIST"]
 
    RECIPIENT = os.environ["RECIPIENT_LIST"]
    recipient_mail_list = RECIPIENT.split(',')
    print(list(recipient_mail_list))

    # Convert message to string and send
    ses_client = boto3.client("ses", region_name="eu-west-2")
    response = ses_client.send_raw_email(
        Source=SENDER,
        Destinations=list(recipient_mail_list),
        RawMessage={'Data': msg.as_string()}
    )
    print(response)
    print("File Path:", file_name)

def PrintException():
    # Print detailed exception information
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    captureErr = "Line No. : " + str(lineno)  + " | ERROR: " + str(exc_obj)
    return captureErr

if __name__ == "__main__":
    main()