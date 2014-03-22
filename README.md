s3_exporter
===========
S3 attachments exporter for hostedredmine.com

Usage
-----
```
/path/to/python2.7 /path/to/run_s3_exporter.py <user_id_from_users_table_id_col>
```

Description
-----------
This script is intended to export the attachments uploaded to S3 bucket from redmine installations. It is particulartly 
written and tested keeping www.hostedremine.com in mind.

Setup/Requirements
------------------
Please install the following if not installed
<ul>
  <li>Python2.7</li>
  <li>Pip - Optional</li>
  <li>Boto</li>
  <li>Mysql.Connector</li>
</ul>

Assumptions
-----------
1. The script outputs to /tmp, so it expects to have write permissions here.

Contact
-------
Please send feedback to Vinay Kumar NP <vinay@askvinay.com>
