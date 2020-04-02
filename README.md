# CloudWatch-IRIS

AWS CloudWatch monitoring for InterSystems IRIS

You can easily publish InterSystems IRIS metrics and Logs to AWS CloudWatch. With metrics and logs in place you can integrate IRIS data into dashboards, alerts etc.

Metrics are based on data, returned by IRIS REST Monitor API https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GCM_rest messages.log is used as a log data source https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=ITECHREF_cconsole_log

## CloudWatch Dashboard with IRIS logs, metrics and EC2 host-level data:
![CloudWatch Dashboard](https://github.com/antonum/CloudWatch-IRIS/blob/master/images/dashboard.png?raw=true)

## IRIS messages.log analyzed with Log Insights
![CloudWatch Log Insights for messages.log](https://github.com/antonum/CloudWatch-IRIS/blob/master/images/log-insights.png?raw=true)

## Installation

Installation assumes the following:
- You are running Amazon Linux 2 instance on EC2
- IRIS version is 2019.4 or later (earlier version does not have MONITOR)
- IRIS is installed in /iris/sys folder
- EC2 instance role allows publishing CloudWatch logs and metrics (you can use CloudWatchAgentServerPolicy for that)

For platforms other than Amazon Linux 2 you can follow this guide to install CloudWatch agent: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/QuickStartEC2Instance.html

For details on creating Ec2 Instance Role with CloudWatch access see: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/create-iam-roles-for-cloudwatch-agent-commandline.html

Install Pyton 3, awslogs client and reqired libraries:

```bash
sudo yum install -y python3
sudo yum install -y awslogs
sudo pip3 install requests boto3

```

Download from repository and copy files to designated folders:

```bash
wget https://raw.githubusercontent.com/antonum/CloudWatch-IRIS/master/iris-monitor-cloudwatch.py
wget https://raw.githubusercontent.com/antonum/CloudWatch-IRIS/master/intersystems-iris.conf
sudo cp iris-monitor-cloudwatch.py /iris/sys/
sudo cp intersystems-iris.conf /etc/awslogs/config/

```

Start monitoring and awslog collection:

```bash
sudo systemctl start awslogsd
sudo systemctl enable awslogsd.service
sudo su
echo "*  *  *  *  * root  python3 /iris/sys/iris-monitor-cloudwatch.py" >> /etc/crontab

```

## Verifying log and metric collection

In AWS CloudWatch check Logs->LogGroups->InterSystems-IRIS. It now should contain entries for your instance. CloudWatch metrics should contain IRIS namespace with InstanceId dimension.

It might take up to 5-10 minutes for the metics and logs to actually show up in CloudWatch

## Troubleshooting

### Logs are not showing up in CloudWatch after 10 minutes

check if awslogd is healthy:
```bash
systemctl status awslogsd

```

### Metrics are not showing in CloudWatch

Check if IRIS Monitor service is running:
```bash
curl http://localhost:52773/api/monitor/metrics
# the output should look like:
...
iris_wd_sleep 10000
iris_wd_temp_queue 73
iris_wd_temp_write 0
iris_wdwij_time 3
iris_wd_write_time 2
iris_wij_writes_per_sec 0

```
If you get an error or timeout - make sure IRIS is running and Monitor service is enabled. Monitor service is avaliable in IRIS versions 2019.4 and later.

Manually run metrics push to CloudWatch:
```bash
python3 /iris/sys/iris-monitor-cloudwatch.py
```
Any error message would indicate problem with metric collection. Healthy system should produce no output.

`Unable to locate credentials` or `AccessDenied` error indicates that EC2 instance IAM role does not allow to publish metrics to CloudWatch. Follow this document to enable it: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/create-iam-roles-for-cloudwatch-agent-commandline.html

Check if cron job is running:

```bash
sudo tail /var/log/cron
# Expected output:
Apr  2 16:35:01 ip-10-0-2-75 CROND[15803]: (root) CMD ( python3 /iris/sys/iris-monitor-cloudwatch.py)
Apr  2 16:36:01 ip-10-0-2-75 CROND[15809]: (root) CMD ( python3 /iris/sys/iris-monitor-cloudwatch.py)
Apr  2 16:37:01 ip-10-0-2-75 CROND[15817]: (root) CMD ( python3 /iris/sys/iris-monitor-cloudwatch.py)
```
Make sure /etc/crontab contains the line: 
```
*  *  *  *  * root  python3 /iris/sys/iris-monitor-cloudwatch.py
```

## Customizing

### IRIS messages.log location

If your messages.log location is different from /iris/sys/mgr/messages.log - adjust intersystems-iris.conf file:
```
[messages.log]
datetime_format = %m/%d/%y-%H:%M:%L
file = /iris/sys/mgr/messages.log
buffer_duration = 5000
log_stream_name = {instance_id}-{hostname}-{ip_address}-messages.log
initial_position = start_of_file
log_group_name = InterSystems-IRIS

```

### Metrics namespace/dimensions

Adjust metricDimension, metricNamespace values in iris-monitor-cloudwatch.py file

```python
...
#Unique Instance Identifier
instanceId=platform.node() #replace with any other way of identifying the instance
metricDimension=instanceId 
metricNamespace='IRIS'
...
```

### Metrics Filter

CloudWatch pricing is based on # of metrics you collect, so it might be a good idea to limit metrics you collect.

The following code in iris-monitor-cloudwatch.py controls which metrics are being pushed to CloudWatch. By default the following metrics are not send to CloudWatch: All the ECP - related metrics, system databse - related metrics and ALT journal.
  
  ```python
  ...# Custom logic to ignore metrics
  recordMetric=True
  ignoreMetrics = ('iris_ecp','_remote_','_rem_', # ignore ECP-related metrics
                  'id="IRISSYS"','id="IRISAUDIT"','id="IRISLOCALDATA"','id="IRISTEMP"', # ignore system databases 
                  'id="secondary"') # ignore secondary journal location
  if any(s in key for s in ignoreMetrics):
    recordMetric=False
  ...
  ```


