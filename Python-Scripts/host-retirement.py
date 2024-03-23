# Import necessary modules
import sys
from datetime import datetime, timezone
import concurrent.futures
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import boto3

# Set up AWS clients
s3_client = boto3.client('s3')
dynamo_client = boto3.client('dynamodb')
sts_client = boto3.client('sts',region_name='eu-west-2')

# Set up date and file information
t = datetime.now(timezone.utc)
today=t.strftime('%Y-%m-%d')
save_path = '/tmp/'
filename = save_path+"RetirementList-"+ today + ".csv"

# Initialize data structures
item_list =[]
dict = {}
acc_event = []

# Record start time
start=datetime.now(timezone.utc).strftime('%H:%M:%S')

# AWS Lambda function handler
def lambda_handler(event,  context):
    # Retrieve items from DynamoDB table using pagination
    MemberRoleTable = os.environ["MEMBER_ROLE_TABLE"]
    paginator = dynamo_client.get_paginator("scan")
    for page in paginator.paginate(TableName=MemberRoleTable):
        for item in page['Items']:
            item_list.append(item)
    main(item_list) 

# Call the main function with the retrieved items  
def main(item_list):
    with concurrent.futures.ThreadPoolExecutor() as e:
        _list=[]
        for item in item_list:
            # Extract necessary information from DynamoDB item
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

                # Submit the retirement report function for parallel execution
                _list.append(e.submit(retirement_report,AccountName,AccountId,credentials,region))
            except:
                print("Error in account logging in :",AccountName)              
                err = PrintException()
                print(err)
        for r in concurrent.futures.as_completed(_list):
            # Aggregate results from parallel executions
            dict.update(r.result())

        result = dict.get('account')
    
    # Write the results to a CSV file
    with open(filename, 'w') as f:  
        print("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % 
              ('AccountName','AccountId','InstanceName','Privateip','InstanceID','InstanceType',
               'Instancestate','InstanceEventId','EventCode','Description','Date'),file=f)
        for res in result:
            print("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % 
                  (res['AccountName'],res['AccountId'],res['InstanceName'],res['PrivateIp'],res['InstanceId'],res['InstanceType'],
                   res['InstanceState'],res['EventId'],res['EventCode'],res['EventDescription'],res['EventDate']),file=f)
    
    # Upload the CSV file to S3
    upload_file(filename)
    
    # Send email with the CSV file attached
    file_name=filename
    send_email_with_attachment(file_name)
    
    # Print start and end time for debugging
    print('Starttime',start)
    print('Endtime',datetime.now(timezone.utc).strftime('%H:%M:%S'))

# Function to retrieve EC2 retirement report for each account
def retirement_report(AccountName,AccountId,credentials,region):
    ACCESS_KEY = credentials['AccessKeyId']
    SECRET_KEY = credentials['SecretAccessKey']
    SESSION_TOKEN = credentials['SessionToken']
    ec2_client = boto3.client('ec2',
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY,
                    region_name=region,aws_session_token=SESSION_TOKEN)

    instancelist = []
    instancename = []
    ec2_filter = [{'Name': 'tag-key','Values': ['Name']}]
    response1 = ec2_client.describe_instances()
    print(AccountName)      
    
    for r in response1['Reservations']:
        for instance in r['Instances']:
            instanceName = ''
            inst_event = {}
            instancestate = instance['State']['Name']
            if not instancestate == "terminated":
                instancestate = instance['State']['Name']
                if 'Tags' in instance: 
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name':
                            instanceName = tag['Value'] 
                    
                instanceID = instance['InstanceId']
                instancestate = instance['State']['Name']
                instanceType = instance['InstanceType']  
                privateip = instance['PrivateIpAddress']
                response = ec2_client.describe_instance_status(InstanceIds=[instanceID])
                
                for resp in response['InstanceStatuses']:
                    if 'Events' in resp:
                        for Event in resp['Events']:
                            inst_event['AccountName'] = AccountName
                            inst_event['AccountId'] = AccountId
                            inst_event['PrivateIp'] = privateip
                            inst_event['InstanceName'] = instanceName
                            inst_event['InstanceId'] = instanceID
                            inst_event['InstanceType'] = instanceType
                            inst_event['InstanceState'] = instancestate
                            inst_event['EventId'] = Event['InstanceEventId']
                            inst_event['EventCode'] = Event['Code']
                            inst_event['EventDescription'] = Event['Description']
                            inst_event['EventDate'] = Event['NotBefore']
                            acc_event.append(inst_event)
    return {'account': acc_event}

# Function to upload file to S3
def upload_file(file_name):
    import datetime
    mydate = datetime.datetime.now()
    Month=mydate.strftime("%B")

    bucket = os.environ["REPORTING_AUTOMATION_BUCKET"]
    object_name='Reports_'+Month+'/'+'Host_Retirement/'+file_name
    object_name = object_name.replace(save_path,"")
    # Upload the file
    s3 = boto3.resource('s3')
    try:
        response = s3.meta.client.upload_file(file_name, bucket, object_name)
    except:
        err = PrintException()
        print(err)

# Function to format HTML content for email
def format_html():
    BODY_HTML = """	<html>
        <head><style>table, th, td { border: 1px solid black;}</style></head>
        <body>
        <p style="font-weight: bold; font-size: 20px; color: red;">LM AWS EC2 Health Events</p>
        <p>Hi All,</p>
        <p>Enclosed is the report providing a list of servers scheduled for retirement or undergoing AWS maintenance. Kindly take appropriate action.</p>
        <p>"""
    
    BODY_Content = BODY_HTML 
    BODY_Content = BODY_Content + """ </p><br>
                  <p>Best Regards,<br>
                  AWS EC2 Health Events Lambda<br>
                  LM CloudOps Automation OBO Sathya Pradeep C
                  </body>
                  </html> """
    return BODY_Content

# Function to send email with attachment
def send_email_with_attachment(file_name):
    # Send email with the generated report attached
    print('Sending the Report to the team..')
    BODY_TEXT = format_html()
    CHARSET = "utf-8"

    # Set message body
    msg = MIMEMultipart('mixed')
    msg["Subject"] = "LM_CloudOps_Automation : Host Retirement"
    bmsg_body = MIMEMultipart('alternative')
    htmlpart = MIMEText(BODY_TEXT, 'html', CHARSET)
    bmsg_body.attach(htmlpart)

    # Attach HTML content
    msg.attach(bmsg_body)

    # Attach the file with a sanitized filename
    sanitized_filename = file_name.replace(save_path, '').replace(":", "-")
    with open(file_name, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={sanitized_filename}")
        msg.attach(part)

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

# Function to print exception details
def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    captureErr = "Line No. : " + str(lineno)  + " | ERROR: " + str(exc_obj)
    return captureErr

# Entry point if the script is run as a standalone module
if __name__ == "__main__":
    main()