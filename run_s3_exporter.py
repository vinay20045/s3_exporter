import sys
import traceback
import mysql.connector
import json
import subprocess
import time
import zipfile
import os

# Some global items

# Load Config File - Expected to be in the same dir as the script.
with open('config.json', 'r') as f:
    config = json.loads(f.read())

# Get S3 Connection to the necessary bucket
import boto
from boto.s3.connection import S3Connection
from boto.s3.key import Key
s3_conn = S3Connection(config['s3_bucket']['access_key'], config['s3_bucket']['secret_access_key'])
s3_bucket = s3_conn.get_bucket(config['s3_bucket']['name'])


def get_file_from_s3(filename, local_path):
    global s3_bucket

    local_file = local_path+'/'+filename
    # Get file from s3 to local path with same name
    try:
        k = Key(s3_bucket)
        k.key = filename
        k.get_contents_to_filename(local_file)
    except:
        with open(local_file, 'w') as f:
            f.write("Something went wrong while getting this file...\n %s" % (sys.exc_info()[1]))

    return local_file


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print """
            Usage: 
                /path/to/python2.7 /path/to/run_s3_exporter.py <user_id_from_users_table_id_col>

            Description: 
                This script is intended to export the attachments uploaded to S3 bucket from redmine installations.
                It is particulartly written and tested keeping www.hostedremine.com in mind.
                Please send feedback to Vinay Kumar NP <vinay@askvinay.com>
            
            Assumptions:
                1. The script outputs to /tmp, so it expects to have write permissions here.
        """
    else:
        try:
            user_id = sys.argv[1]

            # Make the necessary directories, file paths and names
            time_string = str(time.time()).split('.')[0]
            folder_name = time_string+'_'+str(user_id)
            local_path = '/tmp/'+folder_name+'/'
            os.makedirs(local_path)
            zip_file_path = '/tmp/'+folder_name+'.zip'

            # Get db connection
            db_conn = mysql.connector.connect(
                user=config['db']['user'], 
                password=config['db']['password'], 
                host=config['db']['host'], 
                database=config['db']['name']
            )

            # Get project_ids this user is a member of
            db_cursor = db_conn.cursor()
            sql = """
                SELECT 
                    project_id 
                FROM 
                    members 
                WHERE 
                    user_id = '{0}'
            """.format(user_id)
            db_cursor.execute(sql)
            result = db_cursor.fetchall()
            db_cursor.close()
            project_ids = ''
            for row in result:
                project_ids += "'"+str(row[0])+"',"
            project_ids = project_ids.strip(',')
            #print project_ids

            # Get the disk names of attachments that this user can access
            db_cursor = db_conn.cursor()
            sql = """
                SELECT
                    attachments.disk_filename
                FROM
                    attachments
                LEFT JOIN
                    projects ON attachments.container_id = projects.id
                WHERE
                    attachments.container_type = 'Project'
                    AND projects.id IN ({0})
                
                UNION

                SELECT
                    attachments.disk_filename
                FROM
                    attachments
                LEFT JOIN
                    issues ON attachments.container_id = issues.id
                WHERE
                    attachments.container_type = 'Issue'
                    AND issues.project_id IN ({0})

                UNION

                SELECT
                    attachments.disk_filename
                FROM
                    attachments
                LEFT JOIN
                    documents ON attachments.container_id = documents.id
                WHERE
                    attachments.container_type = 'Document'
                    AND documents.project_id IN ({0})

                UNION

                SELECT
                    attachments.disk_filename
                FROM
                    attachments
                LEFT JOIN
                    wikis ON attachments.container_id = wikis.id
                WHERE
                    attachments.container_type = 'WikiPage'
                    AND wikis.project_id IN ({0})

                UNION

                SELECT
                    attachments.disk_filename
                FROM
                    attachments
                LEFT JOIN
                    versions ON attachments.container_id = versions.id
                WHERE
                    attachments.container_type = 'Version'
                    AND versions.project_id IN ({0})

                UNION

                SELECT
                    attachments.disk_filename
                FROM
                    attachments
                LEFT JOIN
                    messages ON attachments.container_id = messages.id
                LEFT JOIN
                    boards ON messages.board_id = boards.id
                WHERE
                    attachments.container_type = 'Messsage'
                    AND boards.project_id IN ({0})
            """.format(project_ids)
            db_cursor.execute(sql)
            result = db_cursor.fetchall()   # Iterate over cursor in case of memory issues.
            db_cursor.close()

            for row in result:
                # get and add the file to zip file
                with zipfile.ZipFile(zip_file_path, 'a') as user_zip:
                    user_zip.write(get_file_from_s3(row[0], local_path))

            # Cleanup
            command = "rm -rf /tmp/%s/" % (folder_name)
            subprocess.call(command, shell=True)
        except:
            print 'Export failed due to the following issue... \n %s \n %s \n %s' %(sys.exc_info()[0], sys.exc_info()[1], traceback.extract_tb(sys.exc_info()[2]))