# Import necessary libraries and modules
import sys
from datetime import datetime,timedelta
import concurrent.futures
from concurrent import futures
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import boto3
import os

# Initialize clients and global variables
s3client = boto3.client('s3')
dynamo_client = boto3.client('dynamodb')
sts_client = boto3.client('sts', region_name='eu-west-2')

today = datetime.today().strftime('%Y-%m-%d')
t = datetime.today().replace(day=1)
tt = datetime.today()
# first = t.strftime('%Y-%m-%d')
first = (tt.replace(day=1) - timedelta(days=1)).replace(day=1)
first = first.strftime('%Y-%m-%d')

#variables for storing information
save_path = '/tmp/'
case_file = save_path + 'LM_AWS_Case_Report' + today + '.csv'

def lambda_handler(event, context):
    # Initialize lists
    item_list = []
    case_list = []

    MemberRoleTable = os.environ["MEMBER_ROLE_TABLE"]
    # Scan DynamoDB table and populate item_list
    paginator = dynamo_client.get_paginator("scan")
    for page in paginator.paginate(TableName=MemberRoleTable):
        for item in page['Items']:
            item_list.append(item)
    main(item_list, case_list)

def main(item_list, case_list):
    print('Script Execution started...')
    # Process items in parallel using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as e:
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
                _list.append(e.submit(get_aws_case, AccountName, AccountId, credentials, case_list))
            except:
                print("Error in account logging in:", AccountName)
                err = PrintException()
                print(err)

        # Wait for all threads to complete
        futures.wait(_list)

    # Generate, upload, and send the report
    print('Generating the report')
    generate_report(case_list)

    file_name = case_file
    upload_file(file_name,case_list)

    send_email_with_attachment(file_name)

def get_aws_case(AccountName,AccountId,credentials,case_list):
    ACCESS_KEY = credentials['AccessKeyId']
    SECRET_KEY = credentials['SecretAccessKey']
    SESSION_TOKEN = credentials['SessionToken']
    session = boto3.session.Session(aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY,region_name='eu-west-2',aws_session_token=SESSION_TOKEN)
    client = session.client('support')
    try:
        response = client.describe_cases(includeResolvedCases=True,afterTime=first,maxResults=100)
        for res in response['cases']:
            oldest_comment_by = None
            oldest_comment_time = None
            SNOW_INC = 'NA'
            for comm in res['recentCommunications']['communications']:
                if oldest_comment_time == None:
                    oldest_comment_time = comm['timeCreated']
                    oldest_comment_by = comm['submittedBy']
                if comm['timeCreated'] >  oldest_comment_time:
                    pass
                else:
                    oldest_comment_time = comm['timeCreated']
                    oldest_comment_by = comm['submittedBy']
                try:
                    if 'INC' in comm['body']:
                        SNOW_INC = comm['body'].split(" ")[1]
                except:
                    err = PrintException()
                    print(err)
            case_dict = {}
            case_dict['AccountName'] =  AccountName
            case_dict['AccountId'] = AccountId
            case_dict['CaseID'] = res['displayId']
            case_dict['Subject'] = res['subject'].replace(","," ").replace("Chat: ",'')
            case_dict['CreatedOn'] = res['timeCreated']
            case_dict['Status'] = res['status']
            case_dict['Service'] = res['serviceCode']
            case_dict['Category'] = res['categoryCode']
            case_dict['Severity'] = res['severityCode']        
            case_dict['SNOWInc'] = SNOW_INC
            case_dict['OldestCommentBy'] = oldest_comment_by.split(' ')[0]
            case_list.append(case_dict)      
    except:
        err = PrintException()
        print(err)
    print('Completed for Account:',AccountName)

# Generate the CSV report
def generate_report(case_list):
    with open(case_file, 'w') as g:
        print("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (
            'AccountName', 'AccountId', 'CaseID', 'Subject', 'Creation Time', 'Status', 'Service', 'Category',
            'Severity', 'SNOW INC', 'Oldest Comment By'), file=g)
        for item in case_list:
            print("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (
                item['AccountName'], item['AccountId'], item['CaseID'], item['Subject'], item['CreatedOn'],
                item['Status'], item['Service'], item['Category'], item['Severity'], item['SNOWInc'],
                item['OldestCommentBy']), file=g)

# Upload the report to S3
def upload_file(file_name,case_list):
    import datetime
    mydate = datetime.datetime.now()
    Month=mydate.strftime("%B")

    bucket = os.environ["REPORTING_AUTOMATION_BUCKET"]
    object_name='Reports_'+Month+'/'+'AWS_Case_Reports/'+file_name
    object_name = object_name.replace(save_path,"")
    # Upload the file
    s3 = boto3.resource('s3')
    try:
        response = s3.meta.client.upload_file(file_name, bucket, object_name)
    except:
        err = PrintException()
        print(err)
    print('Report Generation completed. AWS Cases Found : ',len(case_list))
    End = datetime.datetime.now()
    print("End",End)

# Format HTML content for email body
def format_html():
    # Format HTML content for email body
    BODY_HTML = """	<html>
        <head><style>table, th, td { border: 1px solid black;}</style></head>
        <body>
        <p style="font-weight: bold; font-size: 20px; color: red;">LM AWS Support Cases</p>
        <p>Hi All,</p>
        <p>Please find attached the report which includes the details of AWS Support Cases created.</p>
        <p>"""
    BODY_Content = BODY_HTML 
    BODY_Content = BODY_Content + """ </p><br>
                  <p>Best Regards,<br>
                  AWS Support Case Lambda<br>
                  LM CloudOps Automation OBO Sathya Pradeep C
                  </body>
                  </html> """
    return BODY_Content

# Send email with the generated report attached
def send_email_with_attachment(file_name):
    # Send email with the generated report attached
    print('Sending the Report to the team..')
    BODY_TEXT = format_html()
    CHARSET = "utf-8"

    # Set message body
    msg = MIMEMultipart('mixed')
    msg["Subject"] = "LM_CloudOps_Automation : AWS Support Cases"
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

# Print detailed exception information
def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    captureErr = "Line No. : " + str(lineno)  + " | ERROR: " + str(exc_obj)
    return captureErr

if __name__ == "__main__":
    lambda_handler()

# This Layer is compulsory for this lambda to function. 
# If there is a need to upgrade the Python runtime, please locate the corresponding ARNs for the "PANDAS" and "NUMPY" layers in the provided link based on the desired runtime upgrade.
# https://github.com/keithrozario/Klayers?tab=readme-ov-file#list-of-arns