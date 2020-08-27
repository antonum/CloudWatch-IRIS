# CloudWatch-IRIS

AWS CloudWatchを使用したInterSystems IRISのモニタリング

InterSystems IRISの各種メトリクスとログをAWS CloudWatchに簡単に公開することができます。これらメトリクスとログがあれば、IRISのデータをダッシュボードやアラートなどに統合することができます。

メトリクスは IRIS REST Monitor API が返すデータに基づいています https://docs.intersystems.com/irislatestj/csp/docbook/DocBook.UI.Page.cls?KEY=GCM_rest  
messages.log はログデータソースとして使用されます https://docs.intersystems.com/irislatestj/csp/docbook/DocBook.UI.Page.cls?KEY=ITECHREF_cconsole_log

## IRISのログ、メトリクス及びEC2ホストレベルのデータを統合したCloudWatchダッシュボードの例:
![CloudWatch Dashboard](https://github.com/antonum/CloudWatch-IRIS/blob/master/images/dashboard.png?raw=true)

## IRIS messages.logの分析をログインサイトで行った例
![CloudWatch Log Insights for messages.log](https://github.com/antonum/CloudWatch-IRIS/blob/master/images/log-insights.png?raw=true)

## インストール

インストールは以下を前提としています。
- EC2上でAmazon Linux 2インスタンスを実行している
- IRISのバージョンは2019.4以降（それ以前のバージョンにはMONITOR機能がありません)
- IRISは/iris/sysフォルダにインストールされている
- CloudWatchのログとメトリクスをパブリッシュ可能なEC2インスタンスロールを持つ（そのためにCloudWatchAgentServerPolicyを使用することができます）。

Amazon Linux 2以外のプラットフォームでは、以下のガイドに従ってCloudWatchエージェントをインストールすることができます: https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/logs/QuickStartEC2Instance.html

CloudWatchアクセス用のEC2インスタンスロールを作成する方法の詳細については、https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/monitoring/create-iam-roles-for-cloudwatch-agent-commandline.html を参照してください。

Pyton 3, awslogsクライアント,必要なライブラリをインストールします:

```bash
sudo yum install -y python3
sudo yum install -y awslogs
sudo pip3 install requests boto3

```

レポジトリからファイルをコピーし、所定の場所に配置します:

```bash
wget https://raw.githubusercontent.com/antonum/CloudWatch-IRIS/master/iris-monitor-cloudwatch.py
wget https://raw.githubusercontent.com/antonum/CloudWatch-IRIS/master/intersystems-iris.conf
sudo cp iris-monitor-cloudwatch.py /iris/sys/
sudo cp intersystems-iris.conf /etc/awslogs/config/

```

モニタリング及びawslogによるデータ収集を開始します:

```bash
sudo systemctl start awslogsd
sudo systemctl enable awslogsd.service
sudo su
echo "*  *  *  *  * root  python3 /iris/sys/iris-monitor-cloudwatch.py" >> /etc/crontab

```

## ログとメトリクスの収集を確認

AWS CloudWatchでログ->ロググループ->InterSystems-IRISを確認します。あなたのインスタンスのエントリが含まれているはずです。CloudWatchのメトリクスには、InstanceIdディメンションを持つ、IRISというカスタム名前空間が含まれているはずです。

メトリクスとログが実際にCloudWatchに表示されるまでには5～10分ほどかかるかもしれません。

## トラブルシューティング

### 10分経過してもCloudWatchにログが表示されない場合

awslogdが正常であることを確認します:
```bash
systemctl status awslogsd

```

### CloudWatchにメトリクスが表示されない場合

IRISモニターサービスが稼働していることを確認します:
```bash
curl http://localhost:52773/api/monitor/metrics
# 以下のような出力を得られるはずです:
...
iris_wd_sleep 10000
iris_wd_temp_queue 73
iris_wd_temp_write 0
iris_wdwij_time 3
iris_wd_write_time 2
iris_wij_writes_per_sec 0

```
エラーやタイムアウトが発生した場合は、IRISが起動しており、Monitorサービスが有効になっていることを確認してください。MonitorサービスはIRISのバージョン2019.4以降で利用可能です。

手動でメトリクスをプッシュします:
```bash
python3 /iris/sys/iris-monitor-cloudwatch.py
```
エラーメッセージが出力され場合は、メトリックの収集に問題があることを示しています。正常なシステムでは、出力は発生しないはずです。

`Unable to locate credentials` または `AccessDenied` エラーは、EC2 インスタンスの IAM ロールが CloudWatch へのメトリクスの公開を許可していないことを示しています。このドキュメントに従って有効にしてください: https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/monitoring/create-iam-roles-for-cloudwatch-agent-commandline.html


cronジョブが稼働していることを確認します:
```bash
sudo tail /var/log/cron
# Expected output:
Apr  2 16:35:01 ip-10-0-2-75 CROND[15803]: (root) CMD ( python3 /iris/sys/iris-monitor-cloudwatch.py)
Apr  2 16:36:01 ip-10-0-2-75 CROND[15809]: (root) CMD ( python3 /iris/sys/iris-monitor-cloudwatch.py)
Apr  2 16:37:01 ip-10-0-2-75 CROND[15817]: (root) CMD ( python3 /iris/sys/iris-monitor-cloudwatch.py)
```
/etc/crontabが下記の行を含むことを確認してください: 
```
*  *  *  *  * root  python3 /iris/sys/iris-monitor-cloudwatch.py
```

## カスタマイズ

### IRIS messages.logの場所

messages.logの場所が/iris/sys/mgr/messages.logと異なる場合は - intersystems-iris.confファイルを修正します:
```
[messages.log]
datetime_format = %m/%d/%y-%H:%M:%L
file = /iris/sys/mgr/messages.log
buffer_duration = 5000
log_stream_name = {instance_id}-{hostname}-{ip_address}-messages.log
initial_position = start_of_file
log_group_name = InterSystems-IRIS

```

### メトリクスの名前空間/ディメンション

iris-monitor-cloudwatch.pyファイル内のmetricDimension, metricNamespaceの値を変更します

```python
...
#Unique Instance Identifier
instanceId=platform.node() #replace with any other way of identifying the instance
metricDimension=instanceId 
metricNamespace='IRIS'
...
```

### メトリクスフィルター

CloudWatchの価格設定は、収集したメトリクス数に基づいているので、収集するメトリクスを制限するのは良いアイデアかもしれません。

iris-monitor-cloudwatch.py の以下のコードで、どのメトリクスをCloudWatchにプッシュするかを制御しています。デフォルトでは、次のメトリクスはCloudWatchに送信されません: ECPに関連するすべてのメトリクス、システム・データベースに関連するメトリクス、およびALTジャーナル。
  
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


