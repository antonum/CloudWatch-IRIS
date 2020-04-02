import requests
import boto3
import platform

#Unique Instance Identifier
instanceId=platform.node() #replace with any other way of identifying the instance
metricDimension=instanceId 
metricNamespace='IRIS'

cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
r = requests.get('http://localhost:52773/api/monitor/metrics')
response=r.text
#print(response)
lines=response.split("\n")
totalMetrics=0
metrics = []
nmetrics=0
for line in lines:
  key,valueStr=line.split(" ")
  # print (key, valueStr,"!")
  if "." in valueStr:
    value=float(valueStr)
  else:
    value=int(valueStr) 
  
  # Custom logic to ignore metrics
  recordMetric=True
  ignoreMetrics = ('iris_ecp','_remote_','_rem_', # ignore ECP-related metrics
                  'id="IRISSYS"','id="IRISAUDIT"','id="IRISLOCALDATA"','id="IRISTEMP"', # ignore system databases 
                  'id="secondary"') # ignore secondary journal location
  if any(s in key for s in ignoreMetrics):
    recordMetric=False
  
  if recordMetric:
    metrics.append( {
          'MetricName': key,
          'Dimensions': [
            {
              'Name': 'Instance',
              'Value': instanceId
                }
          ],
          'Unit': 'None',
          'Value': value
      }
    )
    totalMetrics=totalMetrics+1
    nmetrics=nmetrics+1
  if nmetrics>=20:
      response = cloudwatch.put_metric_data(MetricData=metrics,Namespace = metricNamespace)
      metrics = []
      nmetrics=0
#print(metrics)
#print(totalMetrics)

response = cloudwatch.put_metric_data(MetricData=metrics,Namespace = metricNamespace)
#print(response)
