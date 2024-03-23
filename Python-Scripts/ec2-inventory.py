# Import necessary libraries and modules
import sys
from datetime import datetime, timezone
import concurrent.futures
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import boto3

t = datetime.now(timezone.utc)
today = t.strftime('%Y-%m-%d')
day = t.strftime('%a')
time = t.strftime('%H:%M')

# Initialize clients and global variables
s3_client = boto3.client('s3')
dynamo_client = boto3.client('dynamodb')
sts_client = boto3.client('sts', region_name='eu-west-2')

# Initialize lists and variables for storing information
item_list = []
ec2_list = []
save_path = '/tmp/'
filename = save_path + "LM_EC2_Inventory-" + today + ".csv"

def lambda_handler(event, context):
    # Scan DynamoDB table and populate item_list
    MemberRoleTable = os.environ["MEMBER_ROLE_TABLE"]
    paginator = dynamo_client.get_paginator("scan")
    for page in paginator.paginate(TableName=MemberRoleTable):
        for item in page['Items']:
            item_list.append(item)
    main(item_list)

def main(item_list):
    global epoch
    epoch = caluculate_epoch_time()
    # Process items in parallel using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as e:
        _list = []
        # Process each item in DynamoDB  
        for item in item_list:
            # Assume role and gather EC2 information
            indx = item['S No.']['N']
            AccountName = item['Account Name']['S']
            region = item['Region']['S']
            rolearn = item['Role Arn']['S']
            AccountId = item['Account ID']['S']
            try:
                assumed_role = sts_client.assume_role(
                    RoleArn=str(rolearn),
                    RoleSessionName='session')

                credentials = assumed_role['Credentials']
                ACCESS_KEY = credentials['AccessKeyId']
                SECRET_KEY = credentials['SecretAccessKey']
                SESSION_TOKEN = credentials['SessionToken']
                ec2_client = boto3.client('ec2', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY,
                                          region_name=region, aws_session_token=SESSION_TOKEN)
                ssm_client = boto3.client('ssm', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY,
                                          region_name=region, aws_session_token=SESSION_TOKEN)
                _list.append(e.submit(ec2_resp, ec2_client, ssm_client, AccountName, AccountId, region))
                print("is this correct:")
                print(ec2_resp, ec2_client, ssm_client, AccountName, AccountId, region)
            except:
                print("Error processing account:", AccountName)
                err = PrintException()
                print(err)

    # Generate, upload, and send the report
    print('Generating the report')
    genereate_report()
    file_name = filename
    print('Uploading the report to S3....')
    upload_file(file_name)
    print('Updating the DD Table....')
    update_dd_table()
    # if day == 'Mon':
    print('Sending the report via email....')
    send_email_with_attachment(file_name)

def ec2_resp(ec2_client, ssm_client, AccountName, AccountId, region):      
    # Gather EC2 information
    response = ec2_client.describe_instances()
    for r in response['Reservations']:
        for instance in r['Instances']:
            ec2_dict = {}
            vol_list = []
            total_vol_size = 0
            
            instancestate = instance['State']['Name']
            if not instancestate == 'terminated':
                instanceName = ''
                ComputerName = 'NA'
                if 'Tags' in instance: 
                    # collect tagging information of the server
                    instance_tags = {tag['Key']: tag['Value'] for tag in instance['Tags']}
                    instanceName = instance_tags.get('Name', '')
                    environment = instance_tags.get('Environment', instance_tags.get('Env', ''))
                    Role = instance_tags.get('Role', '')
                    Application = instance_tags.get('Application', '')
                    PatchGroup = instance_tags.get('Patch Group', '')
                    Backup = instance_tags.get('Backup', '')
                    Schedule = instance_tags.get('Schedule', '')

                instanceID = instance['InstanceId']
                # Collect AMI information
                ami_id = instance['ImageId']
                ami_name = get_ami_name(ec2_client, ami_id)
                
                # Collect Instance creation time (launch time)
                for eni in instance['NetworkInterfaces']:
                    if eni['Attachment']['DeviceIndex'] == 0:
                        LaunchTime = eni['Attachment']['AttachTime']
                instancestate = instance['State']['Name']
                instanceType = instance['InstanceType']  
                privateip = instance['PrivateIpAddress']
                # Collect Volume count and its size information of the server
                for ebs in instance["BlockDeviceMappings"]:
                    volid = ebs ['Ebs'] ['VolumeId']
                    vol_list.append(volid)
                    ebs_response = ec2_client.describe_volumes(VolumeIds=[volid])
                    for vol_size in ebs_response ['Volumes']:
                        size = vol_size['Size']
                        total_vol_size = total_vol_size + size
                # Collect Platform type, computer name information of the server from SSM
                Platfm = ssm_client.describe_instance_information(Filters=[{'Key': 'InstanceIds','Values': [instanceID]}])
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
                            if P == 'ComputerName':
                                ComputerName = Plat['ComputerName']
              
                ec2_dict['AccountName'] = AccountName
                ec2_dict['AccountId'] = AccountId
                ec2_dict['InstanceName'] = instanceName
                ec2_dict['PrivateIp'] = privateip
                ec2_dict['InstanceID'] = instanceID
                ec2_dict['InstanceType'] = instanceType
                ec2_dict['Instancestate'] = instancestate
                ec2_dict['PlatformName'] = PlatformName
                ec2_dict['Platform'] = Platform
                ec2_dict['ComputerName'] = ComputerName
                ec2_dict['Environment'] = environment
                ec2_dict['Role'] = Role
                ec2_dict['Application'] = Application
                ec2_dict['PatchGroup'] = PatchGroup
                ec2_dict['Backup'] = Backup
                ec2_dict['Schedule'] = Schedule
                ec2_dict['Region'] = region
                ec2_dict['LaunchTime'] = str(LaunchTime)
                ec2_dict['TotalVolumes'] = len(vol_list)
                ec2_dict['TotalVolumesSize'] = total_vol_size
                ec2_dict['AMI_ID'] = ami_id
                ec2_dict['AMI_NAME'] = ami_name
                
                ec2_list.append(ec2_dict)
    print('Completed for the Account ', AccountName)

def get_ami_name(ec2_client, ami_id):
    # Function to retrieve AMI Name given AMI ID
    try:
        response = ec2_client.describe_images(ImageIds=[ami_id])
        ami_name = response['Images'][0]['Name']
        return ami_name
    except Exception as e:
        print(f"Error fetching AMI Name for AMI ID {ami_id}: {e}")
        return "Unknown"

def genereate_report():
    # Generate the CSV report
    with open(filename, 'w') as f: 
        print("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % 
              ('AccountName','AccountId','InstanceName','Privateip','InstanceID','InstanceType','Instancestate','PlatformType','Platform','ComputerName',
               'Environment','Role','Application','PatchGroup','Backup','Schedule','Launch Time','TotalVolumes','TotalVolumesSize', 'AMI_NAME/AMI_ID'),file=f)
        for ec2 in ec2_list:
            # Concatenate AMI Name and ID into one column
            ami_details = f"{ec2['AMI_NAME']}/{ec2['AMI_ID']}"
            print("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % 
                  (ec2['AccountName'],ec2['AccountId'],ec2['InstanceName'],ec2['PrivateIp'],ec2['InstanceID'],ec2['InstanceType'],ec2['Instancestate'],ec2['Platform'],ec2['PlatformName'],ec2['ComputerName'],
                   ec2['Environment'],ec2['Role'],ec2['Application'],ec2['PatchGroup'],ec2['Backup'],ec2['Schedule'],ec2['LaunchTime'],ec2['TotalVolumes'],ec2['TotalVolumesSize'], ami_details),file=f)   

def upload_file(file_name):
    # Upload the report to S3
    import datetime
    mydate = datetime.datetime.now()
    Month = mydate.strftime("%B")
    # bucket='lm-cloudops-automation-reports'
    bucket = os.environ["REPORTING_AUTOMATION_BUCKET"]
    object_name = 'Reports_' + Month + '/' + 'Ec2_Inventory/' + file_name
    object_name = object_name.replace(save_path, "")
    s3 = boto3.resource('s3')
    try:
        response = s3.meta.client.upload_file(file_name, bucket, object_name)
    except:
        err = PrintException()
        print("Error uploading file to S3:", err)

def update_dd_table():
    # Update DynamoDB table with EC2 information
    dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table('ec2_inventory_lm')
    table = dynamodb.Table(os.environ["EC2_INVENTORY_DYNAMODB_TABLE"])
    for ec2 in ec2_list:
        try:
            response = table.put_item(Item={
                'AccountName': str(ec2['AccountName']),
                'AccountId': str(ec2['AccountId']),
                'Region': str(ec2['Region']),
                'InstanceName': ec2['InstanceName'],
                'InstanceID': ec2['InstanceID'],
                'InstanceType': ec2['InstanceType'],
                'Instancestate': ec2['Instancestate'],
                'PlatformType': ec2['Platform'],
                'Platform': ec2['PlatformName'],
                'ComputerName': ec2['ComputerName'],
                'Environment': ec2['Environment'],
                'Role': ec2['Role'],
                'Application': ec2['Application'],
                'PatchGroup': ec2['PatchGroup'],
                'Backup': ec2['Backup'],
                'Schedule': ec2['Schedule'],
                'PrivateIp': ec2['PrivateIp'],
                'Launched On': ec2['LaunchTime'],
                'TotalVolumes': ec2['TotalVolumes'],
                'TotalVolumesSize': ec2['TotalVolumesSize'],
                'AMI_NAME': ec2['AMI_NAME'],
                'AMI_ID': ec2['AMI_ID'],
                'TTL': epoch
            } 
            )
        except:
            print(PrintException())
            print("Error during table.put_item, Error updating DynamoDB table")
            response = "Error"

def format_html():
    # Format HTML content for email body
    BODY_HTML = """ <html>
        <head><style>table, th, td { border: 1px solid black;}</style></head>
        <body>
        <p style="font-weight: bold; font-size: 20px; color: red;">LM AWS EC2 Inventory</p>
        <p>Hi All,</p>
        <p>PFA report containing AWS EC2 Inventory report </p>
        <p>"""
    BODY_Content = BODY_HTML 
    BODY_Content = BODY_Content + """ </p><br>
                  <p>Best Regards,<br>
                  AWS EC2 Inventory Lambda<br>
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
    msg["Subject"] = "LM_CloudOps_Automation : AWS EC2 Inventory"
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

    # Fetching sender and receiver email from ENV Variables
    SENDER = os.environ["SENDER_LIST"]
    RECIPIENT = os.environ["RECIPIENT_LIST"]
    recipient_mail_list = RECIPIENT.split(',')
    print(list(recipient_mail_list))

    # Convert message to string and send
    ses_client = boto3.client("ses", region_name="eu-west-2")
    response = ses_client.send_raw_email(
        Source=str(SENDER),
        Destinations=list(recipient_mail_list),
        RawMessage={'Data': msg.as_string()}
    )
    print(response)
    print("File Path:", file_name)

def caluculate_epoch_time():
    # Calculate epoch time for DynamoDB TTL
    import time
    from datetime import datetime, timedelta
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow = tomorrow.strftime('%d.%m.%Y %H:%M:%S')
    pattern = '%d.%m.%Y %H:%M:%S'
    epoch = int(time.mktime(time.strptime(tomorrow, pattern)))
    return epoch

def PrintException():
    # Print detailed exception information
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    captureErr = "Line No. : " + str(lineno) + " | ERROR: " + str(exc_obj)
    return captureErr

if __name__ == "__main__":
    main()