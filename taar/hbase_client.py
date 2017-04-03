import contextlib
import json
import boto3
from happybase import Connection


class HBaseClient:
    _hostname = None

    def __init__(self):
        self.tablename = 'main_summary'
        self.column_family = b'cf'
        self.column = b'cf:payload'
        if HBaseClient._hostname is None:
            HBaseClient._hostname = self._get_master_address()
            print(HBaseClient._hostname)

    def _get_master_address(self):
        client = boto3.client('ec2')
        reservations = client.describe_instances(Filters=[
            {'Name': 'tag:Name', 'Values': ['telemetry-hbase']},
            {
                'Name': 'tag:aws:elasticmapreduce:instance-group-role',
                'Values': ['MASTER']
            }
        ])["Reservations"]

        if len(reservations) == 0:
            raise Exception("HBase master not found!")

        if len(reservations) > 1:
            raise Exception("Multiple HBase masters found!")

        return reservations[0]["Instances"][0]["NetworkInterfaces"][0]["PrivateIpAddress"]

    def get_client_profile(self, client_id):
        """Retrieve the latest row for the given client in HBase

        Only the last known version of the info is retrieved"""
        with contextlib.closing(Connection(self._hostname)) as connection:
            table = connection.table(self.tablename)
            row_start = "{}:{}".format(client_id, "99999999")
            for key, data in table.scan(row_start=row_start, limit=1,
                                        columns=[self.column_family],
                                        reverse=True):
                return json.loads(data[self.column].decode("utf-8"))
        return None