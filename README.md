# CloudWatch-IRIS
Configuring AWS CloudWatch with InterSystems IRIS

## Installation

Install Pyton 3, awslogs client and reqired libraries:

sudo yum install -y python3
sudo yum install -y awslogs
sudo pip3 install requests boto3

Clone repository and copy files to designated folders:

sudo cp iris-monitor-cloudwatch.py /iris/sys/
sudo cp  intersystems-iris.conf /etc/awslogs/config/

Start monitoring and awslog collection:

sudo systemctl start awslogsd
sudo systemctl enable awslogsd.service
sudo echo "*  *  *  *  * root  python3 /iris/sys/iris-monitor-cloudwatch.py" >> /etc/crontab


