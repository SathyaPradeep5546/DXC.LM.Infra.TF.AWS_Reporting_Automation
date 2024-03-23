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

# Inform the user about the ongoing process
print("Please wait while we fetch the Events info and save it to AWS_Health-date.csv....")

# Initialize necessary variables and clients
item_list = []
eventlist = []
s3_client = boto3.client('s3')
dynamo_client = boto3.client('dynamodb')
sts_client = boto3.client('sts',region_name='eu-west-2')

# Get the current date and set up the filename for the CSV report
t = datetime.now(timezone.utc)
today=t.strftime('%Y-%m-%d')
save_path = '/tmp/'
filename = save_path+"AWS_Health_Events-"+ today +".csv"

# Initialize a list to store AWS Health Events
acc_event = []
start=datetime.now(timezone.utc).strftime('%H:%M:%S')

# Define the Lambda handler function
def lambda_handler(event,  context):
    # Use DynamoDB paginator to retrieve items from a table
    MemberRoleTable = os.environ["MEMBER_ROLE_TABLE"]
    paginator = dynamo_client.get_paginator("scan")
    for page in paginator.paginate(TableName=MemberRoleTable):
        for item in page['Items']:
            item_list.append(item)
    main(item_list) 

# Define the main function
def main(item_list) :
    with concurrent.futures.ThreadPoolExecutor() as e:
        _list=[]
        for item in item_list:
            # Extract necessary information from DynamoDB items
            indx = item['S No.']['N']
            AccountName = item['Account Name']['S']
            region = item['Region']['S']
            rolearn = item['Role Arn']['S']
            AccountId = item['Account ID']['S']
            try:
                # Assume a role using STS and submit the task to the ThreadPoolExecutor
                assumed_role = sts_client.assume_role(RoleArn=str(rolearn),RoleSessionName='session')
                credentials=assumed_role['Credentials']
                _list.append(e.submit(retirement_report,AccountName,AccountId,credentials,region))
            except:
                print("Error in account logging in :",AccountName)              
                err = PrintException()
                print(err)
    # Generate the report, upload it, send an email with an attachment, and print start and end times
    gen_report(eventlist)
    upload_file(filename)
    file_name=filename
    send_email_with_attachment(file_name)
    print('Starttime',start)
    print('Endtime',datetime.now(timezone.utc).strftime('%H:%M:%S'))

# Define a function to fetch and process AWS Health Events
def retirement_report(AccountName,AccountId,credentials,region):
    print(AccountName)
    inst_event = {}
    ACCESS_KEY = credentials['AccessKeyId']
    SECRET_KEY = credentials['SecretAccessKey']
    SESSION_TOKEN = credentials['SessionToken']

    # Create a client for AWS Health using assumed role credentials
    client = boto3.client('health',aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY,region_name='us-east-1',aws_session_token=SESSION_TOKEN)
  
    try:
        eventresponse = client.describe_events()
    except:
        err = PrintException()
        print(err)

    # Process each event and extract relevant information
    for event in eventresponse['events']:
        event_arn = event['arn']
        response = client.describe_event_details(eventArns=[event_arn])
        for eve in response['successfulSet']: 
            statusCode = eve['event']['statusCode']
            if not statusCode == 'closed':
                event_dict = {}
                event_dict['AccountName'] = AccountName
                event_dict['AccountId'] = AccountId
                event_dict['region']  = eve['event']['region']
                event_dict['eventTypeCode'] = eve['event'] ['eventTypeCode']
                event_dict['eventTypeCategory']= eve['event']['eventTypeCategory']
                event_dict['eventScopeCode']= eve['event']['eventScopeCode']
                event_dict['startTime']= eve['event']['startTime']
                event_dict['eventDescription'] = str(eve['eventDescription']).replace(',','').encode("utf-8")
                try:
                    event_dict['endTime']= eve['event']['endTime']
                except:
                    event_dict['endTime'] = 'NA'
                try:
                    event_dict['lastUpdatedTime'] = eve['event']['lastUpdatedTime']
                except:
                    event_dict['lastUpdatedTime'] = 'NA'
                event_dict['statusCode'] = eve['event']['statusCode']
                try:
                    event_dict['eventaz']= eve['event']['availabilityZone']
                except:
                    event_dict['eventaz'] = 'NA'
                res_response = client.describe_affected_entities(filter={'eventArns':[event_arn]})
                affected_list = []
                for res in res_response['entities']:
                    try:
                        event_dict['entityArn'] = res['entityArn']
                    except:
                        event_dict['entityArn'] = 'NA'
                    try:
                        affected_list.append(res['entityValue'])                        
                    except:
                        event_dict['entityValue'] = 'NA'
                event_dict['entityValue'] = str(affected_list).replace(',',' | ')
                eventlist.append(event_dict)

# Define a function to generate the CSV report
def gen_report(eventlist):
    with open(filename, 'w') as f:
        print("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % 
              ('Account Name','Account ID','Region','EventTypeCode','EventScopeCode','StartTime','EndTime',
               'LastUpdatedTime','StatusCode','EventAZ','ResourceId','Description'),file=f)
        for sub in eventlist:
            print("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % 
                  (sub['AccountName'],sub['AccountId'],sub['region'],sub['eventTypeCode'],sub['eventScopeCode'],sub['startTime'],sub['endTime'],
                   sub['lastUpdatedTime'],sub['statusCode'],sub['eventaz'],sub['entityValue'],sub['eventDescription']),file=f)

# Define a function to upload the CSV file to S3
def upload_file(file_name):
    import datetime
    mydate = datetime.datetime.now()
    Month=mydate.strftime("%B")

    bucket = os.environ["REPORTING_AUTOMATION_BUCKET"]
    object_name='Reports_'+Month+'/'+'AWS_Health_Events/'+file_name
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
        <p style="font-weight: bold; font-size: 20px; color: red;">LM AWS Health Events</p>
        <p>Hi All,</p>
        <p>Please find attached a report listing AWS Health Events. Kindly take appropriate measures accordingly.</p>
        <p>"""
    
    BODY_Content = BODY_HTML 
    BODY_Content = BODY_Content + """ </p><br>
                  <p>Best Regards,<br>
                  AWS AWS Health Events Lambda<br>
                  LM CloudOps Automation OBO Sathya Pradeep C
                  </body>
                  </html> """
    return BODY_Content

# Define a function to send an email with an attachment
def send_email_with_attachment(file_name):
    # Send email with the generated report attached
    print('Sending the Report to the team..')
    BODY_TEXT = format_html()
    CHARSET = "utf-8"

    # Set message body
    msg = MIMEMultipart('mixed')
    msg["Subject"] = "LM_CloudOps_Automation : AWS Health Events"
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

#Functions for printing any exceptions or errors
def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    captureErr = "Line No. : " + str(lineno)  + " | ERROR: " + str(exc_obj)
    return captureErr

# Entry point of the script
if __name__ == "__main__":
    main()