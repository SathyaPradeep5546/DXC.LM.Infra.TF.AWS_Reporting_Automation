# Import necessary libraries and modules
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

# Get the current time in UTC
t = datetime.now(timezone.utc)
today = t.strftime('%Y-%m-%d')

# Initialize AWS clients for S3, DynamoDB, and STS
s3_client = boto3.client('s3')
dynamo_client = boto3.client('dynamodb')
sts_client = boto3.client('sts', region_name='eu-west-2')

# Initialize lists and variables for storing information
item_list = []
ec2_list = []   # List to store EC2 instance information
acc_list = []   # List to store aggregated account information

# Set up paths and filenames for storing reports
save_path = '/tmp/'
filename = save_path + "Patch_Scan_Report.csv"
accfilename = save_path + "Account_Patch_Compliance.csv"

# Lambda function entry point
def lambda_handler(event, context):
    # Use DynamoDB paginator to handle large scan result sets
    MemberRoleTable = os.environ["MEMBER_ROLE_TABLE"]
    paginator = dynamo_client.get_paginator("scan")
    for page in paginator.paginate(TableName=MemberRoleTable):
        for item in page['Items']:
            item_list.append(item)
    main(item_list)

# Main function orchestrating the process
def main(item_list):
    # Use ThreadPoolExecutor for concurrent execution of tasks
    with concurrent.futures.ThreadPoolExecutor() as e:
        _list = []
        for item in item_list:
            # Extract account information from the DynamoDB item
            indx = item['S No.']['N']
            AccountName = item['Account Name']['S']
            region = item['Region']['S']
            rolearn = item['Role Arn']['S']
            AccountId = item['Account ID']['S']
            try:
                # Assume the role to get temporary credentials
                assumed_role = sts_client.assume_role(
                    RoleArn=str(rolearn),
                    RoleSessionName='session'
                )
                credentials = assumed_role['Credentials']
                ACCESS_KEY = credentials['AccessKeyId']
                SECRET_KEY = credentials['SecretAccessKey']
                SESSION_TOKEN = credentials['SessionToken']
                
                # Create EC2 and SSM clients using temporary credentials
                ec2_client = boto3.client('ec2', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name=region, aws_session_token=SESSION_TOKEN)
                ssm_client = boto3.client('ssm', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name=region, aws_session_token=SESSION_TOKEN)
                
                # Submit EC2 response task to ThreadPoolExecutor
                _list.append(e.submit(ec2_resp, ec2_client, ssm_client, AccountName, AccountId))
            except:
                print("Error in account logging in:", AccountName)
                err = PrintException()
                print(err)

    print('Generating the reports......')
    generate_instance_patch_report()
    generate_account_patch_complaince_report()
    
    file_names = [filename, accfilename] 
    print('Uploading the report to S3')
    upload_file(file_names)
    
    print('Sending the report via email....')
    send_email_with_attachment(file_names)

# Function to handle EC2 responses
def ec2_resp(ec2_client, ssm_client, AccountName, AccountId):
    # Lists to store various EC2 instances for patch compliance
    instance_list = []
    win_instance_list = []
    lin_instance_list = []
    non_comp_instance_list = []
    non_comp_win_instance_list = []
    non_comp_lin_instance_list = []

    # Get EC2 instance information
    response = ec2_client.describe_instances()
    try:
        for r in response['Reservations']:
            for instance in r['Instances']:
                ec2_dict = {}
                instancestate = instance['State']['Name']
                
                if not instancestate == 'terminated':
                    instanceName = ''
                    if 'Tags' in instance:
                        for tag in instance['Tags']:
                            if tag['Key'] == 'Name':
                                instanceName = tag['Value']

                    instanceID = instance['InstanceId']
                    instance_list.append(instanceID)
                    instancestate = instance['State']['Name']
                    instanceType = instance['InstanceType']
                    privateip = instance['PrivateIpAddress']
                    
                    # Get platform information using SSM
                    Platfm = ssm_client.describe_instance_information(Filters=[{'Key': 'InstanceIds', 'Values': [instanceID]},])
                    if Platfm['InstanceInformationList'] == []:
                        if 'Platform' in instance:
                            Platform = instance['Platform']
                            PlatformName = instance['Platform']
                        else:
                            Platform = 'Linux'
                            PlatformName = 'Linux'
                    else:
                        for Plat in Platfm['InstanceInformationList']:
                            for P in Plat:
                                if P == "PlatformName":
                                    PlatformName = Plat['PlatformName']
                                elif P == "PlatformType":
                                    Platform = Plat['PlatformType']

                    # Get missing patches for the instance
                    response = ssm_client.describe_instance_patches(InstanceId=instanceID, Filters=[{'Key': 'State', 'Values': ['Missing',]},])
                    title = ''
                    MissingKB = ''
                    Class = ''
                    Sev = ''
                    State = ''
                    Compliance = ''
                    patchlist = []

                    # Check patch compliance
                    if response['Patches'] == []:
                        Compliance = "Compliant"
                    else:
                        for patch in response['Patches']:
                            patch_dict = {}
                            patch_dict['Title'] = patch['Title'].encode("utf-8")
                            patch_dict['MissingKB'] = patch['KBId']
                            Class = patch['Classification']

                            if Class == 'Security' or Class == 'Critical' or Class == 'Bugfix' or Class == 'SecurityUpdates':
                                Compliance = "Non-Compliant"
                                patch_dict_str = str(patch_dict).replace(",", " ").replace("{", "").replace("}", "")
                                patchlist.append(patch_dict_str)
                            else:
                                Compliance = "Compliant"

                    # Categorize instances based on platform and compliance
                    if Platform.lower() == 'windows':
                        win_instance_list.append(instanceID)
                    else:
                        lin_instance_list.append(instanceID)

                    if Compliance == "Non-Compliant" and Platform.lower() == 'windows':
                        non_comp_win_instance_list.append(instanceID)
                        non_comp_instance_list.append(instanceID)
                    elif Compliance == "Non-Compliant" and not Platform.lower() == 'windows':
                        non_comp_lin_instance_list.append(instanceID)
                        non_comp_instance_list.append(instanceID)
                    else:
                        pass

                    # Populate EC2 instance information dictionary
                    ec2_dict['AccountName'] = AccountName
                    ec2_dict['AccountId'] = AccountId
                    ec2_dict['instanceName'] = instanceName
                    ec2_dict['privateip'] = privateip
                    ec2_dict['instanceID'] = instanceID
                    ec2_dict['instanceType'] = instanceType
                    ec2_dict['instancestate'] = instancestate
                    ec2_dict['PlatformName'] = PlatformName
                    ec2_dict['Platform'] = Platform
                    if not patchlist == []:
                        ec2_dict['Missing_Patch_Details'] = str(patchlist).replace(",", "||")
                    else:
                        ec2_dict['Missing_Patch_Details'] = '-'
                    ec2_dict['Missing_Patch_Count'] = str(len(patchlist))
                    ec2_dict['Compliance'] = Compliance

                    # Append EC2 instance information to the list
                    ec2_list.append(ec2_dict)
    except:
        err = PrintException()
        print(err)

    # Calculate account-level patch compliance
    acc_dict = {}
    try:
        acc_comp = calculate_account_comp(win_instance_list, non_comp_win_instance_list, lin_instance_list, non_comp_lin_instance_list)
    except:
        err = PrintException()
        print(err)

    # Populate account information dictionary
    acc_dict['AccountName'] = AccountName
    acc_dict['AccountId'] = AccountId
    acc_dict['AverageCompliance'] = acc_comp['Avg_Complaince']
    acc_dict['WindowsPatchCompliance'] = acc_comp['Win_Complaince']
    acc_dict['LinuxPatchCompliance'] = acc_comp['Lin_Complaince']
    acc_dict['TotalServers'] = len(instance_list)
    acc_dict['Non-Compliant_Servers'] = len(non_comp_instance_list)
    print('Completed for the Account ', AccountName)

    # Append account information to the list
    acc_list.append(acc_dict)

# Calculate account-level patch compliance
def calculate_account_comp(win_instance_list, non_comp_win_instance_list, lin_instance_list, non_comp_lin_instance_list):
    acc_comp = {}
    WindowsCompliance = 'NA'
    LinuxCompliance = 'NA'
    avg_compliance = 'NA'

    if not len(win_instance_list) == 0:
        WindowsCompliance = (len(win_instance_list) - len(non_comp_win_instance_list)) / len(win_instance_list) * 100
    if not len(lin_instance_list) == 0:
        LinuxCompliance = (len(lin_instance_list) - len(non_comp_lin_instance_list)) / len(lin_instance_list) * 100

    if not LinuxCompliance == 'NA' and not WindowsCompliance == 'NA':
        avg_compliance = (int(WindowsCompliance + LinuxCompliance)) / 2
    elif LinuxCompliance == 'NA' and WindowsCompliance == 'NA':
        avg_compliance = 'NA'
    elif WindowsCompliance == 'NA' and not LinuxCompliance == 'NA':
        avg_compliance = LinuxCompliance
    elif LinuxCompliance == 'NA' and not WindowsCompliance == 'NA':
        avg_compliance = WindowsCompliance

    acc_comp['Win_Complaince'] = WindowsCompliance
    acc_comp['Lin_Complaince'] = LinuxCompliance
    acc_comp['Avg_Complaince'] = avg_compliance
    return acc_comp

# Generate account-level patch compliance report
def generate_account_patch_complaince_report():
    with open(accfilename, 'w') as g:
        print("%s,%s,%s,%s,%s,%s,%s" % ('AccountName', 'AccountId', 'Avg Patch Compliance %', 'Windows Patch Compliance %', 'Linux Patch Compliance %', 'TotalServers', 'Non-Compliant_Servers'), file=g)
        for acc in acc_list:
            print("%s,%s,%s,%s,%s,%s,%s" % (
                acc['AccountName'], acc['AccountId'], acc['AverageCompliance'], acc['WindowsPatchCompliance'],
                acc['LinuxPatchCompliance'], acc['TotalServers'], acc['Non-Compliant_Servers']), file=g)

# Generate EC2 instance-level patch compliance report
def generate_instance_patch_report():
    with open(filename, 'w') as f:
        print("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (
            'AccountName', 'AccountId', 'InstanceName', 'Privateip', 'InstanceID', 'InstanceType', 'Instancestate',
            'PlatformType', 'Platform', 'Compliance', 'Missing_Patch_Details', 'Missing_Patch_Count'), file=f)
        for ec2 in ec2_list:
            print("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (
                ec2['AccountName'], ec2['AccountId'], ec2['instanceName'], ec2['privateip'], ec2['instanceID'],
                ec2['instanceType'], ec2['instancestate'], ec2['Platform'], ec2['PlatformName'], ec2['Compliance'],
                ec2['Missing_Patch_Details'], ec2['Missing_Patch_Count']), file=f)

# Upload the generated file to S3
def upload_file(file_names):
    import datetime
    mydate = datetime.datetime.now()
    Month = mydate.strftime("%B")

    bucket = os.environ["REPORTING_AUTOMATION_BUCKET"]
    for file_name in file_names:
        object_name = 'Reports_' + Month + '/' + 'LM_Patch_Reports/' + file_name
        object_name = object_name.replace(save_path, "")
        
        # Upload the file to S3 bucket
        s3 = boto3.resource('s3')
        try:
            response = s3.meta.client.upload_file(file_name, bucket, object_name)
        except:
            err = PrintException()
            print(err)

def format_html():
    # Format HTML content for email body
    BODY_HTML = """	<html>
        <head><style>table, th, td { border: 1px solid black;}</style></head>
        <body>
        <p style="font-weight: bold; font-size: 20px; color: red;">LM AWS Patch Scan and Compliance Report</p>
        <p>Hi All,</p>
        <p>Please find attached the report which includes both the Patch Scan Report and the Patch Compliance Report.</p>
        <p>"""
    BODY_Content = BODY_HTML 
    BODY_Content = BODY_Content + """ </p><br>
                  <p>Best Regards,<br>
                  AWS Patch Scan Lambda<br>
                  LM CloudOps Automation OBO Sathya Pradeep C
                  </body>
                  </html> """
    return BODY_Content

def send_email_with_attachment(file_names):
    # Send email with the generated report attached
    print('Sending the Report to the team..')
    BODY_TEXT = format_html()
    CHARSET = "utf-8"

    # Set message body
    msg = MIMEMultipart('mixed')
    msg["Subject"] = "LM_CloudOps_Automation : Patch Scan and Compliance Report"
    bmsg_body = MIMEMultipart('alternative')
    htmlpart = MIMEText(BODY_TEXT, 'html', CHARSET)
    bmsg_body.attach(htmlpart)

    # Attach HTML content
    msg.attach(bmsg_body)

    # Attach multiple files with sanitized filenames
    for file_name in file_names:
        sanitized_filename = file_name.replace(save_path, '').replace(":", "-")
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
    print("File Path:", file_names)

# Function to print the exception details
def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    captureErr = "Line No. : " + str(lineno) + " | ERROR: " + str(exc_obj)
    return captureErr