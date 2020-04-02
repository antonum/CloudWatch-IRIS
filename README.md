# CloudWatch-IRIS
Configuring AWS CloudWatch with InterSystems IRIS

## Installation

Installation assumes the following:
- You are running Amazon Linux 2 instance on EC2
- IRIS is installed in /iris/sys folder
- EC2 instance role allows publishing CloudWatch logs and metrics (you can use CloudWatchAgentServerPolicy for that)

Install Pyton 3, awslogs client and reqired libraries:

```
sudo yum install -y python3
sudo yum install -y awslogs
sudo pip3 install requests boto3
```

Clone repository and copy files to designated folders:

```
git clone https://github.com/antonum/CloudWatch-IRIS.git
sudo cp CloudWatch-IRIS/iris-monitor-cloudwatch.py /iris/sys/
sudo cp CloudWatch-IRIS/intersystems-iris.conf /etc/awslogs/config/
```

Start monitoring and awslog collection:

```
sudo systemctl start awslogsd
sudo systemctl enable awslogsd.service
sudo echo "*  *  *  *  * root  python3 /iris/sys/iris-monitor-cloudwatch.py" >> /etc/crontab
```

